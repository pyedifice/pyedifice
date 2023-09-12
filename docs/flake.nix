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
      pythonWithPackages = pkgs.python310.withPackages (p: with p; [
          sphinx-book-theme
        ]);
    in
    {
      devShells = {
        default = pythonWithPackages.env;
      };
    });
}
