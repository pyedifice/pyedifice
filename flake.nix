{
  inputs = {
    # Before we try to upgrade nixpkgs we better make sure this is fixed:
    # https://github.com/nix-community/poetry2nix/issues/1291#issuecomment-1702272801
    nixpkgs.url = "github:nixos/nixpkgs/nixos-23.05";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = inputs: inputs.flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import inputs.nixpkgs {
        inherit system;
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
      poetryEnvAttrs = {
        projectDir = ./.;
        preferWheels = true;
        overrides = pkgs.poetry2nix.overrides.withDefaults (pyfinal: pyprev:
          let
            qt6-libs = [
              pkgs.libxkbcommon
              pkgs.qt6.full
              pkgs.gtk3
              pkgs.speechd
              pkgs.gst
              pkgs.gst_all_1.gst-plugins-base
              pkgs.gst_all_1.gstreamer
              pkgs.postgresql.lib
              pkgs.unixODBC
              pkgs.pcsclite
            ];
          in

          {
            pyqt6-qt6 = pyprev.pyqt6-qt6.overridePythonAttrs (old: {
              autoPatchelfIgnoreMissingDeps = [ "libmysqlclient.so.21" ];
              buildInputs = old.buildInputs ++ qt6-libs;
            });
            pyqt6 = pyprev.pyqt6.overridePythonAttrs (old: {
              autoPatchelfIgnoreMissingDeps = [ "libmysqlclient.so.21" ];
              buildInputs = old.buildInputs ++ qt6-libs;
            });
            pyside6-essentials = pyprev.pyside6-essentials.overridePythonAttrs (old: {
              autoPatchelfIgnoreMissingDeps = [ "libmysqlclient.so.21" "libmimerapi.so" ];
              preBuild = ''
                addAutoPatchelfSearchPath ${pyfinal.shiboken6}/${pyfinal.python.sitePackages}/shiboken6
              '';
              buildInputs = old.buildInputs ++ qt6-libs;
              postInstall = ''
                rm -r $out/${pyfinal.python.sitePackages}/PySide6/__pycache__
              '';
            });
            pyside6-addons = pyprev.pyside6-addons.overridePythonAttrs (old: {
              autoPatchelfIgnoreMissingDeps = [ "libmysqlclient.so.21" "libmimerapi.so" "libQt6Quick3DSpatialAudio.so.6" ];
              preBuild = ''
                addAutoPatchelfSearchPath ${pyfinal.shiboken6}/${pyfinal.python.sitePackages}/shiboken6
                addAutoPatchelfSearchPath ${pyfinal.pyside6-essentials}/${pyfinal.python.sitePackages}/PySide6
              '';
              buildInputs = old.buildInputs ++ qt6-libs;
              postInstall = ''
                rm -r $out/${pyfinal.python.sitePackages}/PySide6/__pycache__
              '';
            });
          });
        python = pkgs.python310;
      };
      poetryEnv = pkgs.poetry2nix.mkPoetryEnv (poetryEnvAttrs // {
        editablePackageSources = {
          edifice = ./edifice;
        };
        extras = [ "*" ];
        extraPackages = ps: with ps; [
          pip
          sphinx-book-theme
          sphinx-autodoc-typehints
        ];
      });
    in
    {
      # There are 3 devShell flavors here.
      #
      # 1. nix develop .#default
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
      #        poetry install --sync --all-extras --no-root
      #        poetry shell
      #        ./run_tests.sh
      #
      # 3. nix develop .#poetry2nix
      #
      #    https://github.com/nix-community/poetry2nix#mkpoetryenv
      #    environment with editable edifice/ source files.

      #    In this environment the tests should pass.
      #
      #        ./run_tests.sh
      #
      devShells = {

        default = inputs.self.devShells.${system}.poetry2nix;
        nixpkgs = pythonEnv;

        poetry = pkgs.mkShell {
          packages = [ pkgs.poetry pkgs.qt6.qtbase ];
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

        poetry2nix = poetryEnv.env.overrideAttrs (oldAttrs: {
          buildInputs = [ pkgs.nodePackages.pyright ];
        });

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
                text = "python -m edifice --inspect examples/calculator.py Calculator";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
          example-forms =
            let
              script = pkgs.writeShellApplication {
                name = "edifice-example";
                runtimeInputs = [
                  (pkgs.poetry2nix.mkPoetryEnv poetryEnvAttrs)
                ];
                text = "PYTHONPATH=. python examples/form.py";
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
                    extraPackages = ps: with ps; [
                      pandas
                      yfinance
                      matplotlib
                    ];
                  }))
                ];
                text = "python -m edifice --inspect examples/financial_charts.py App";
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
                text = "python -m edifice --inspect examples/harmonic_oscillator.py Oscillator";
              };
            in
            {
              type = "app";
              program = "${script}/bin/edifice-example";
            };
        };
    });
}
