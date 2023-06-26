{ lib
, buildPythonPackage
, fetchPypi
, pytest
, qasync
, pyside2
, watchdog
, numpy
, pyqt5
}:

buildPythonPackage rec {
    pname = "pyedifice";
    version = "0.0.10";

    # src = pkgs.fetchPypi {
    #   inherit pname version;
    #   sha256 = "sha256-u46Ca/UgEuoAQ9HHQZmYgX/htUEbxp3XaVEXZ3iMZdI=";
    # };

    src = ../..;

    propagatedBuildInputs = [ 
      qasync
      pyside2
      pyqt5
      watchdog
      numpy
    ];

    doCheck = false;

  meta = with lib; {
    description = "declarative GUI library for Python";
    homepage = "https://github.com/xc-jp/pyedifice";
    license = licenses.mit;
    maintainers = with maintainers; [ ];
  };
}
