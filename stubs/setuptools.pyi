import typing


def setup(name: str,
          version: str,
          author: str,
          author_email: str,
          description: str,
          long_description: str,
          long_description_content_type: str,
          url: str,
          packages: typing.List[str],
          python_requires: str,
          entry_points: typing.Dict[str, typing.List[str]],
          install_requires: typing.List[str],
          package_data: typing.Dict[str, typing.List[str]]
          ) -> None:
    ...


def find_packages() -> typing.List[str]:
    ...
