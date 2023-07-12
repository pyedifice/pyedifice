{
  inputs = {
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
            qasync = pyself.pythonPackages.callPackage qasync_ {};
            pyedifice = pyself.pythonPackages.callPackage pyedifice_ {};
          };
        in pkgs.python310.override { inherit packageOverrides; self = pythonOverride; };


      pythonWithPackages = pythonOverride.withPackages (p: with p; [
        pip # for reading dependency information with pip list
        pytest
        qasync
        pyside6
        pyqt6
        matplotlib
        watchdog
      ]);

      # https://github.com/NixOS/nixpkgs/issues/80147#issuecomment-784857897
      qtOverride = attrs: attrs // {
        QT_PLUGIN_PATH = with pkgs.qt6; "${qtbase}/${qtbase.qtPluginPrefix}";
      };

      pythonEnv = qtOverride pythonWithPackages.env;

      # pythonEnv = pythonWithPackages.env.overrideAttrs(finalAttrs: prevAttrs: {
      #   # https://github.com/NixOS/nixpkgs/issues/80147#issuecomment-784857897
      #   QT_PLUGIN_PATH = with pkgs.qt6; "${qtbase}/${qtbase.qtPluginPrefix}";
      # });
    in
    rec {
      devShells = {
        default = pythonEnv;
        poetry = pkgs.mkShell {
          packages= [ pkgs.python310 pkgs.poetry pkgs.qt6.qtbase ];
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
      };
      lib = {
        qasync = qasync_;
        pyedifice = pyedifice_;
      };
      # apps = {
      #   test = {
      #     type = "app";
      #     program = (pythonOverride.withPackages (p: [p.pyedifice]).env) // {
      #       shellHook = ''
      #         ./run_tests.sh
      #         '';
      #       };
      #   };
      # };
    });
}

