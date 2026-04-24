# /// script
# requires-python = ">=3.12"
# dependencies = ["garminconnect>=0.3.3"]
# ///
import getpass
import pathlib

from garminconnect import Garmin

client = Garmin(
    input("Garmin email: "),
    getpass.getpass("Garmin password: "),
    prompt_mfa=lambda: input("MFA code: "),
)
client.login("~/.garminconnect")
print(pathlib.Path.home().joinpath(".garminconnect", "garmin_tokens.json").read_text())
