{ lib
, buildPythonPackage
, fetchPypi
}:

buildPythonPackage rec {
  pname = "qasync";
  version = "0.13.0"; # latest is 0.24.0
  src = fetchPypi {
    inherit pname version;
    # sha256 = "sha256-5YPRw64g/RLrCN7jWMUncJtIDnjVf7cu5XqUCXMH2Vk="; 0.24.0
    sha256 = "sha256-B6GUqfF3Bu7JCFlrOkC0adLL+BwbnTOVNXpMkQRLovI=";
  };
  doCheck = false;
}

