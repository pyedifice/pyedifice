{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
    uv2nix = {
      url = "github:considerate/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs-unstable";
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
                # pyside6-essentials = pysuper.pyside6-essentials.overridePythonAttrs( old: {
                #   autoPatchelfIgnoreMissingDeps = old.autoPatchelfIgnoreMissingDeps or [ ] ++ [
                #     "libgbm.so.1"
                #   ];
                #   # propagatedBuildInputs = old.propagatedBuildInputs or [] ++ [
                #   #   prev.mesa # provides libgbm.so.1
                #   # ];
                # });
                # pyside6-addons = pysuper.pyside6-addons.overridePythonAttrs( old: {
                #   autoPatchelfIgnoreMissingDeps = old.autoPatchelfIgnoreMissingDeps or [ ] ++ [
                #     "libgbm.so.1"
                #   ];
                # });
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
      pkgs-unstable = inputs.nixpkgs-unstable.legacyPackages.${system};
      uv2nix = inputs.uv2nix.lib.uv2nixFor { pkgs = pkgs-unstable; };
      python-uv = uv2nix.uv2nix {
        src = ./.;
        modules = [
          ({ python, ... }: {
            distributions.pyedifice.extra-dev-dependencies.dev = [ python.pkgs.unittestCheckHook ];
            uv.overlays = [
              (final: prev: {
                pyedifice = prev.pyedifice.overridePythonAttrs (old: {
                  unittestFlagsArray = [ "-s" "tests" ];
                  QT_QPA_PLATFORM_PLUGIN_PATH = "${final.pkgs.qt6.qtbase}/lib/qt-6/plugins/platforms";
                  buildInputs = (old.buildInputs or [ ]) ++ [
                    final.pkgs.qt6.qtbase
                    final.pkgs.qt6.qtwayland
                    final.pkgs.qt6.qtwayland.dev
                    final.pkgs.libxkbcommon
                    final.pkgs.gtk3
                    final.pkgs.speechd
                    final.pkgs.gst
                    final.pkgs.gst_all_1.gst-plugins-base
                    final.pkgs.gst_all_1.gstreamer
                    final.pkgs.postgresql.lib
                    final.pkgs.unixODBC
                    final.pkgs.pcsclite
                    final.pkgs.xorg.libxcb
                    final.pkgs.xorg.xcbutil
                    final.pkgs.xorg.xcbutilcursor
                    final.pkgs.xorg.xcbutilerrors
                    final.pkgs.xorg.xcbutilimage
                    final.pkgs.xorg.xcbutilkeysyms
                    final.pkgs.xorg.xcbutilrenderutil
                    final.pkgs.xorg.xcbutilwm
                    final.pkgs.libdrm
                    final.pkgs.pulseaudio
                  ];
                  nativeBuildInputs = old.nativeBuildInputs ++ [
                    final.pkgs.qt6.wrapQtAppsHook
                  ];
                });
                pyside6-essentials = prev.pyside6-essentials.overridePythonAttrs (old: pkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
                  autoPatchelfIgnoreMissingDeps = [ "libmysqlclient.so.21" "libmimerapi.so" "libQt6EglFsKmsGbmSupport.so*" ];
                  preFixup = ''
                    addAutoPatchelfSearchPath ${final.shiboken6}/${final.python.sitePackages}/shiboken6
                  '';
                  buildInputs = old.buildInputs or [ ] ++ [
                    final.pkgs.qt6.full
                    final.pkgs.qt6.qtwayland
                    final.pkgs.qt6.qtwayland.dev
                    final.pkgs.libxkbcommon
                    final.pkgs.gtk3
                    final.pkgs.speechd
                    final.pkgs.gst
                    final.pkgs.gst_all_1.gst-plugins-base
                    final.pkgs.gst_all_1.gstreamer
                    final.pkgs.postgresql.lib
                    final.pkgs.unixODBC
                    final.pkgs.pcsclite
                    final.pkgs.xorg.libxcb
                    final.pkgs.xorg.xcbutil
                    final.pkgs.xorg.xcbutilcursor
                    final.pkgs.xorg.xcbutilerrors
                    final.pkgs.xorg.xcbutilimage
                    final.pkgs.xorg.xcbutilkeysyms
                    final.pkgs.xorg.xcbutilrenderutil
                    final.pkgs.xorg.xcbutilwm
                    final.pkgs.libdrm
                    final.pkgs.pulseaudio
                  ];
                  nativeBuildInputs = old.nativeBuildInputs ++ [
                    final.pkgs.qt6.wrapQtAppsHook
                  ];
                  pythonImportsCheck = [
                    "PySide6"
                    "PySide6.QtCore"
                  ];
                  postInstall = ''
                    python -c 'import PySide6; print(PySide6.__all__)'
                  '';
                });

                pyside6-addons = prev.pyside6-addons.overridePythonAttrs (old: pkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
                  autoPatchelfIgnoreMissingDeps = [
                    "libmysqlclient.so.21"
                    "libmimerapi.so"
                  ];
                  preFixup = ''
                    addAutoPatchelfSearchPath ${final.shiboken6}/${final.python.sitePackages}/shiboken6
                    addAutoPatchelfSearchPath ${final.pyside6-essentials}/${final.python.sitePackages}/PySide6
                    addAutoPatchelfSearchPath $out/${final.python.sitePackages}/PySide6
                  '';
                  buildInputs = (old.buildInputs or [ ]) ++ [
                    final.pkgs.nss
                    final.pkgs.xorg.libXtst
                    final.pkgs.alsa-lib
                    final.pkgs.xorg.libxshmfence
                    final.pkgs.xorg.libxkbfile
                    #
                    final.pkgs.gtk3
                    final.pkgs.speechd
                    final.pkgs.gst
                    final.pkgs.gst_all_1.gst-plugins-base
                    final.pkgs.gst_all_1.gstreamer
                    final.pkgs.pcsclite
                  ];
                });
                pyside6 = prev.pyside6.overridePythonAttrs (_old: {
                  # The PySide6/__init__.py script tries to find the Qt libraries
                  # relative to its own path in the installed site-packages directory.
                  # This then fails to find the paths from pyside6-essentials and
                  # pyside6-addons because they are installed into different directories.
                  #
                  # To work around this issue we symlink all of the files resulting from
                  # those packages into the aggregated `pyside6` output directories.
                  #
                  # See https://github.com/nix-community/poetry2nix/issues/1791 for more details.
                  dontWrapQtApps = true;
                  postFixup = ''
                    ${pkgs.xorg.lndir}/bin/lndir ${final.pyside6-essentials}/${final.python.sitePackages}/PySide6 $out/${final.python.sitePackages}/PySide6
                    ${pkgs.xorg.lndir}/bin/lndir ${final.pyside6-addons}/${final.python.sitePackages}/PySide6 $out/${final.python.sitePackages}/PySide6
                  '';
                });
              })
            ];
          })
        ];
        python = pkgs-unstable.python313;
        preferWheels = true;
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

        uv =
          let
            libraries = [
              pkgs.libGL
              pkgs.stdenv.cc.cc
              pkgs.glib
              pkgs.zlib
              "/run/opgengl-driver"
              pkgs.libxkbcommon
              pkgs.fontconfig
              pkgs.xorg.libX11
              pkgs.freetype
              pkgs.dbus
            ];
            library-path = pkgs.lib.makeLibraryPath libraries;
            python-base = pkgs.python313;
            python = pkgs.callPackage "${pkgs.path}/pkgs/development/interpreters/python/wrapper.nix" {
              python = python-base;
              requiredPythonModules = python-base.pkgs.requiredPythonModules;
              makeWrapperArgs = [
                "--inherit-argv0"
                "--prefix"
                "LD_LIBRARY_PATH"
                ":"
                library-path
              ];
            };
          in
          pkgs.mkShell {
            packages = [ python pkgs-unstable.uv ];
          };

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
          buildInputs = [ pkgs.nodePackages.pyright pkgs.nixd ];
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
        inherit python-uv;
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
