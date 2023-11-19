{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
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
        overlays = [ inputs.poetry2nix.overlay ];
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
        # We cannot currently specify the python version because of
        # https://github.com/nix-community/poetry2nix/issues/1076
        projectDir = ./.;
        preferWheels = true;
        overrides = pkgs.poetry2nix.overrides.withDefaults (pyfinal: pyprev: { });
      };
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
          python=pkgs.python310;
          extras = [ "*" ];
          extraPackages = ps: with ps; [
            pip

            # sphinx packages for make docs
            sphinx-book-theme
            sphinx-autodoc-typehints

            # pandas, yfinance, matplotlib for running examples/financial_charts.py
            pandas
            yfinance
            matplotlib
          ];
        })).env.overrideAttrs (oldAttrs: {
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
                    extraPackages = ps: with ps; [
                      pandas
                      yfinance
                      matplotlib
                    ];
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
