{ lib
, buildPythonPackage
, pytest
, qasync
, pyside6
, pyqt6
, watchdog
, numpy
}:

buildPythonPackage rec {
  pname = "pyedifice";
  version = "0.0.10";

  # src = pkgs.fetchPypi {
  #   inherit pname version;
  #   sha256 = "sha256-u46Ca/UgEuoAQ9HHQZmYgX/htUEbxp3XaVEXZ3iMZdI=";
  # };

  # src = ../..;

  # src = lib.cleanSourceWith {
  #   src = ../..;
  #   filter = path: _: builtins.elem path [
  #     "edifice"
  #     "LICENSE"
  #     "README.md"
  #     "requirements.txt"
  #     "setup.py"
  #   ];
  # };

  # src = lib.sources.sourceByRegex ../.. [
  #   "edifice/.*\\.py"
  #   "LICENSE"
  #   "README\\.md"
  #   "requirements\\.txt"
  #   "setup\\.py"
  # ];

  src = lib.cleanSourceWith {
    src = lib.cleanSource ../..;
    filter = path: _type: ! (builtins.elem (builtins.baseNameOf path) [
      "__pycache__"
      "flake.nix"
      "flake.lock"
    ]);
  };

  propagatedBuildInputs = [
    qasync
    pyside6
    pyqt6
    watchdog
    numpy
  ];

  doCheck = false;

  meta = with lib; {
    description = "declarative GUI library for Python";
    homepage = "https://github.com/pyedifice/pyedifice";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
