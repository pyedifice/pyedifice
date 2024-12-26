{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };
  outputs = inputs: inputs.flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [
          inputs.poetry2nix.overlays.default
          # https://github.com/nix-community/poetry2nix?tab=readme-ov-file#creating-a-custom-poetry2nix-instance
          (final: prev: {
            poetry2nix = prev.poetry2nix.overrideScope (p2nixfinal: p2nixprev: {
              defaultPoetryOverrides = p2nixprev.defaultPoetryOverrides.extend (pyself: pysuper: {
                #
                # This section might be needed for upgrading to PySide6 v6.7.2
                #
                pyside6-essentials = pysuper.pyside6-essentials.overridePythonAttrs( old: {
                  autoPatchelfIgnoreMissingDeps = old.autoPatchelfIgnoreMissingDeps or [ ] ++ [
                    "libgbm.so.1"
                  ];
                  # propagatedBuildInputs = old.propagatedBuildInputs or [] ++ [
                  #   prev.mesa # provides libgbm.so.1
                  # ];
                });
                pyside6-addons = pysuper.pyside6-addons.overridePythonAttrs( old: {
                  autoPatchelfIgnoreMissingDeps = old.autoPatchelfIgnoreMissingDeps or [ ] ++ [
                    "libgbm.so.1"
                    "libQt6WebViewQuick.so.6"
                  ];
                });
              });
            });
          })

          (_final: prev: {
            # https://github.com/NixOS/nixpkgs/blob/release-23.11/doc/languages-frameworks/python.section.md#how-to-override-a-python-package-for-all-python-versions-using-extensions-how-to-override-a-python-package-for-all-python-versions-using-extensions
            pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
              (
                _pyfinal: pyprev: {
                  # eventlet = pyprev.eventlet.overridePythonAttrs (oldAttrs: {
                  #   disabledTests = oldAttrs.disabledTests ++ [
                  #     "test_full_duplex"
                  #     "test_invalid_connection"
                  #     "test_nonblocking_accept_mark_as_reopened"
                  #     "test_raised_multiple_readers"
                  #     "test_recv_into_timeout"
                  #   ];
                  # });
                }
              )
            ];
          })
          (final: prev: {
            poetry = prev.poetry.override { python3 = final.python310; };
          })
        ];
      };

      qasync_ = import ./nix/qasync/default.nix;
      pyedifice_ = import ./nix/pyedifice/default.nix;

      # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md#overriding-python-packages-overriding-python-packages
      pythonOverride =
        let
          # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md#including-a-derivation-using-callpackage-including-a-derivation-using-callpackage
          packageOverrides = pyself: pysuper: {
            qasync = pyself.pythonPackages.callPackage qasync_ { };
            pyedifice = pyself.pythonPackages.callPackage pyedifice_ { };
          };
        in
        pkgs.python310.override { inherit packageOverrides; self = pythonOverride; };

      pythonWithPackages = pythonOverride.withPackages (p: with p; [
        pip # for reading dependency information with pip list
        pytest
        qasync
        pyside6
        pyqt6
        matplotlib
        watchdog
        sphinx-book-theme
        sphinx-autodoc-typehints
      ]);

      qtOverride = attrs: attrs // {
        # https://github.com/NixOS/nixpkgs/issues/80147#issuecomment-784857897
        QT_PLUGIN_PATH = with pkgs.qt6; "${qtbase}/${qtbase.qtPluginPrefix}";
      };

      pythonEnv = qtOverride pythonWithPackages.env;

      repo-root =
        let
          env-root = builtins.getEnv "REPO_ROOT";
        in
        if env-root != "" then env-root else ./.;
      poetryEnvAttrs = {
        python = pkgs.python310;
        projectDir = ./.;
        preferWheels = true;
        # The repo-root is for `nix develop --impure`.
        editablePackageSources = {
          pyedifice = repo-root;
        };
      };
    in
    {
      # There are 3 devShell flavors here.
      #
      # 1. nix develop .#pythonEnv
      #
      #    Nixpkgs pythonWithPackages environment.
      #    In this environment the tests should pass.
      #
      #        ./run_tests.sh
      #
      # 2. nix develop .#poetry
      #
      #    Poetry environment.
      #    In this environment the tests should pass.
      #
      #        poetry shell
      #        poetry install --sync --all-extras
      #        ./run_tests.sh
      #
      # 3. nix develop .#poetry2nix (default)
      #
      #    https://github.com/nix-community/poetry2nix#mkpoetryenv
      #    environment with editable edifice/ source files.

      #    In this environment the tests should pass.
      #
      #        ./run_tests.sh
      #
      devShells = rec {

        # default = inputs.self.devShells.${system}.poetry2nix;

        inherit pythonEnv;

        poetry = pkgs.mkShell {
          packages = [ pkgs.python310 pkgs.poetry pkgs.qt6.qtbase ];
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
              ];
            in
            ''
              # fixes libstdc++ issues and libgl.so issues
              export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath libraries}"
              # https://github.com/NixOS/nixpkgs/issues/80147#issuecomment-784857897
              export QT_PLUGIN_PATH="${pkgs.qt6.qtbase}/${pkgs.qt6.qtbase.qtPluginPrefix}"
              echo "Enter the poetry shell with"
              echo ""
              echo "    poetry shell"
              echo ""
            '';
        };

        poetry2nix = (pkgs.poetry2nix.mkPoetryEnv (poetryEnvAttrs // {
          extras = [ "*" ];
          extraPackages = ps: with ps; [ ];
        })).env.overrideAttrs (oldAttrs: {
          buildInputs = [ pkgs.nodePackages.pyright pkgs.nixd];
          # Need LC_ALL for the `make html` command in the docs/ directory
          # because of https://github.com/sphinx-doc/sphinx/issues/11739
          LC_ALL = "C.UTF-8";
          # Need PYTHONPATH for VS Code Debugger mode so that we run pyedifice
          # in the source tree, not in the Nix store. It's not enough to get
          # changes with editablePackageSources; we also want to set breakpoints.
          PYTHONPATH = ".";
        });

        default = poetry2nix;

      };

      lib = {
        # TODO discuss flake `outputs.lib` overlays for `qasync` and `pyedifice`
        # in the README or somewhere.
        qasync = qasync_;
        pyedifice = pyedifice_;
      };

      apps =
        let
          run_tests_sh = pkgs.writeScript "run_tests_sh" (builtins.readFile ./run_tests.sh);
        in
        {
          run_tests =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-run-tests";
                runtimeInputs = [
                  (pkgs.poetry2nix.mkPoetryEnv poetryEnvAttrs)
                ];
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
                  (pkgs.poetry2nix.mkPoetryEnv poetryEnvAttrs)
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
                runtimeInputs = [
                  (pkgs.poetry2nix.mkPoetryEnv poetryEnvAttrs)
                ];
                text = "cd ${inputs.self.outPath}; python examples/calculator.py";
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
                runtimeInputs = [
                  (pkgs.poetry2nix.mkPoetryEnv (poetryEnvAttrs // {
                    extraPackages = ps: with ps; [ ];
                  }))
                ];
                text = "cd ${inputs.self.outPath}; python examples/financial_charts.py";
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
                runtimeInputs = [
                  (pkgs.poetry2nix.mkPoetryEnv poetryEnvAttrs)
                ];
                text = "cd ${inputs.self.outPath}; python examples/harmonic_oscillator.py";
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
                runtimeInputs = [
                  (pkgs.poetry2nix.mkPoetryEnv poetryEnvAttrs)
                ];
                text = "cd ${inputs.self.outPath}; python examples/todomvc.py";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
        };
    });
}
