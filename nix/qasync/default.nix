{ lib
, buildPythonPackage
, fetchPypi
}:

buildPythonPackage rec {
  pname = "qasync";
  version = "0.24.0";
  src = fetchPypi {
    inherit pname version;
    sha256 = "sha256-5YPRw64g/RLpCN7jWMUncJtIDnjVf7cu5XqUCXMH2Vk=";
  };
  doCheck = false;
}

