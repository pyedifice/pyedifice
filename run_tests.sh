set -euo pipefail
echo "Test with PySide6"
python -m unittest discover -s tests
echo "Test with PyQt6"
EDIFICE_QT_VERSION=PyQt6 python -m unittest discover -s tests
