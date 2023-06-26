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

      # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md#overriding-python-packages-overriding-python-packages
      python-extras =
        let
          # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md#including-a-derivation-using-callpackage-including-a-derivation-using-callpackage
          packageOverrides = pyself: pysuper: {
            qasync =
              (pyself.pythonPackages.callPackage (import ./nix/qasync/default.nix) {});
            pyedifice =
              (pyself.pythonPackages.callPackage (import ./nix/pyedifice/default.nix) {});
          };
        # https://stackoverflow.com/questions/51333232/nixos-how-do-i-get-get-a-python-with-debug-info-included-with-packages
        # in pkgs.python310.override { inherit packageOverrides; self = pkgs.enableDebugging python-extras; };
        in pkgs.python310.override { inherit packageOverrides; self = python-extras; };


      pythonWithPackages = python-extras.withPackages (p: with p; [
        pip # for reading dependency information with pip list
        pytest
        qasync
        # pyedifice
        pyside6
        pyqt6
        matplotlib
        watchdog
      ]);
    in
    {
      devShells = {
        default = pythonWithPackages.env.overrideAttrs(finalAttrs: prevAttrs: {
          # https://github.com/NixOS/nixpkgs/issues/80147#issuecomment-784857897
          QT_PLUGIN_PATH = with pkgs.qt6; "${qtbase}/${qtbase.qtPluginPrefix}";
        });
      };
    });
}

