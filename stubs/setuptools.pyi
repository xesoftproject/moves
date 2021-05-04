from typing import Dict
from typing import List
from typing import Optional

def setup(name: str,
          version: str,
          author: str,
          author_email: str,
          description: str,
          long_description: str,
          long_description_content_type: str,
          url: str,
          packages: List[str],
          python_requires: str,
          entry_points: Dict[str, List[str]],
          install_requires: List[str],
          package_data: Optional[Dict[str, List[str]]]=None) -> None:
    ...


def find_packages() -> List[str]:
    ...
