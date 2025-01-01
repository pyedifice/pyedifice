# https://github.com/pyproject-nix/uv2nix/blob/e4f7193604cf1af77094034fb5e278cf0e1920ae/templates/hello-world/flake.nix
{
  description = "Edifice flake using uv2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix_hammer_overrides.url = "github:TyberiusPrime/uv2nix_hammer_overrides";
    uv2nix_hammer_overrides.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      uv2nix_hammer_overrides,
      ...
    }:
    let
      inherit (nixpkgs) lib;

      # Load a uv workspace from a workspace root.
      # Uv2nix treats all uv projects as workspace projects.
      # https://pyproject-nix.github.io/uv2nix/lib/workspace.html
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Create package overlay from workspace.
      overlay = workspace.mkPyprojectOverlay {
        # Prefer prebuilt binary wheels as a package source.
        # Sdists are less likely to "just work" because of the metadata missing from uv.lock.
        # Binary wheels are more likely to, but may still require overrides for library dependencies.
        sourcePreference = "wheel"; # or sourcePreference = "sdist";
        # Optionally customise PEP 508 environment
        # environ = {
        #   platform_release = "5.10.65";
        # };
      };

      # This example is only using x86_64-linux
      pkgs = nixpkgs.legacyPackages.x86_64-linux;

      # Extend generated overlay with build fixups
      #
      # Uv2nix can only work with what it has, and uv.lock is missing essential metadata to perform some builds.
      # This is an additional overlay implementing build fixups.
      # See:
      # - https://pyproject-nix.github.io/uv2nix/FAQ.html

      pyprojectOverrides = final: prev: {
        # Implement build fixups here.
      };

      # Use Python 3.10 from nixpkgs
      python = pkgs.python310;

      # Construct package set
      pythonSet =
        # Use base package set from pyproject.nix builders
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.default
              overlay
              pyprojectOverrides
              # Currently uv2nix_hammer_overrides breaks the build
              # because it overrides final.pyside6-essentials.
              # (uv2nix_hammer_overrides.overrides pkgs)
              (import ./pyproject-overrides.nix pkgs)
            ]
          );

    in
    {
      # Package a virtual environment as our main application.
      #
      # Enable no optional dependencies for production build.
      packages.x86_64-linux.default = pythonSet.mkVirtualEnv "edifice-env" workspace.deps.default;

      # This example provides two different modes of development:
      # - Impurely using uv to manage virtual environments
      # - Pure development using uv2nix to manage virtual environments
      devShells.x86_64-linux = rec {

        default = uv2nix;

        # It is of course perfectly OK to keep using an impure virtualenv workflow and only use uv2nix to build packages.
        # This devShell simply adds Python and undoes the dependency leakage done by Nixpkgs Python infrastructure.
        impure = pkgs.mkShell {
          packages = [
            python
            pkgs.uv
          ];
          shellHook =
            let
              libraries = [
                pkgs.libGL
                pkgs.stdenv.cc.cc.lib
                pkgs.glib
                pkgs.zlib
                "/run/opgengl-driver"
                pkgs.libxkbcommon
                pkgs.fontconfig
                pkgs.xorg.libX11
                pkgs.freetype
                pkgs.dbus

                pkgs.xorg.libxcb
                pkgs.xorg.xcbutil
                pkgs.xorg.xcbutilcursor
                pkgs.xorg.xcbutilerrors
                pkgs.xorg.xcbutilimage
                pkgs.xorg.xcbutilkeysyms
                pkgs.xorg.xcbutilrenderutil
                pkgs.xorg.xcbutilwm

                pkgs.zstd
              ];
            in
            ''
              # fixes libstdc++ issues and libgl.so issues
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath libraries}"
              # https://github.com/NixOS/nixpkgs/issues/80147#issuecomment-784857897
              export QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}"
              # export QT_DEBUG_PLUGINS=1

              # uv2nix environment settings
              unset PYTHONPATH
              export UV_PYTHON_DOWNLOADS=never

              echo ""
              echo "    uv venv"
              echo "    source .venv/bin/activate"
              echo "    uv sync --all-extras"
              echo ""

            '';
        };

        # This devShell uses uv2nix to construct a virtual environment purely from Nix, using the same dependency specification as the application.
        # The notable difference is that we also apply another overlay here enabling editable mode ( https://setuptools.pypa.io/en/latest/userguide/development_mode.html ).
        #
        # This means that any changes done to your local files do not require a rebuild.
        uv2nix =
          let
            # Create an overlay enabling editable mode for all local dependencies.
            editableOverlay = workspace.mkEditablePyprojectOverlay {
              # Use environment variable
              root = "$REPO_ROOT";
              # Optional: Only enable editable for these packages
              # members = [ "hello-world" ];
            };

            # Override previous set with our overrideable overlay.
            editablePythonSet = pythonSet.overrideScope editableOverlay;

            # Build virtual environment, with local packages being editable.
            #
            # Enable all optional dependencies for development.
            virtualenv = editablePythonSet.mkVirtualEnv "edifice-dev-env" workspace.deps.all;

          in
          pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv
              pkgs.pyright
              pkgs.nixd
            ];
            shellHook = ''
              # Undo dependency propagation by nixpkgs.
              unset PYTHONPATH

              # Don't create venv using uv
              export UV_NO_SYNC=1

              # Prevent uv from downloading managed Python's
              export UV_PYTHON_DOWNLOADS=never

              # Get repository root using git. This is expanded at runtime by the editable `.pth` machinery.
              export REPO_ROOT=$(git rev-parse --show-toplevel)

              # # Need LC_ALL for the `make html` command in the docs/ directory
              # # because of https://github.com/sphinx-doc/sphinx/issues/11739
              # LC_ALL = "C.UTF-8";
              # # Need PYTHONPATH for VS Code Debugger mode so that we run pyedifice
              # # in the source tree, not in the Nix store. It's not enough to get
              # # changes with editablePackageSources; we also want to set breakpoints.
              # PYTHONPATH = ".";
            '';
          };
      };

      apps.x86_64-linux =
        let
          run_tests_sh = pkgs.writeScript "run_tests_sh" (builtins.readFile ./run_tests.sh);
          virtualenv-all = pythonSet.mkVirtualEnv "edifice-env" workspace.deps.all;
        in
        {
          run_tests =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-run-tests";
                runtimeInputs = [ virtualenv-all ];
                text = "${run_tests_sh}";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-run-tests";
            };
          run_tests-virtualX =
            let
              script-virtualX = pkgs.writeShellApplication {
                name = "edifice-run-tests";
                runtimeInputs = [
                  virtualenv-all
                  pkgs.xvfb-run
                ];
                text = "xvfb-run ${run_tests_sh}";
              };
            in
            {
              type = "app";
              program = "${script-virtualX}/bin/edifice-run-tests";
            };
          example-calculator =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-example";
                runtimeInputs = [ virtualenv-all ];
                text = "python ${inputs.self.outPath}/examples/calculator.py";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
          example-financial-charting =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-example";
                runtimeInputs = [ virtualenv-all ];
                text = "python ${inputs.self.outPath}/examples/financial_charts.py";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
          example-harmonic-oscillator =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-example";
                runtimeInputs = [ virtualenv-all ];
                text = "python ${inputs.self.outPath}/examples/harmonic_oscillator.py";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
          example-todomvc =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-example";
                runtimeInputs = [ virtualenv-all ];
                text = "python ${inputs.self.outPath}/examples/todomvc.py";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
        };
    };
}
