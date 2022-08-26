import pathlib
# this ensures it will work with python 3.7 and up
try:
    # for python 3.11 and up
    import tomllib              # type: ignore
except ModuleNotFoundError:
    # for 3.7 <= python < 3.11
    import tomli as tomllib     # type: ignore


bwp_file_name = pathlib.Path(__file__).parent / 'bwp_config.toml'
with bwp_file_name.open(mode='rb') as file_handler:
    bwp_config = tomllib.load(file_handler)
