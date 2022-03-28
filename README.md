# zoom-bot

An app to pull the latest zoom meeting matching a defined description for a user's account, and posting a link to Slack, tagging pertinent users.

## AWS Installation/Update

The bot is run from AWS Lambda. 

The `lambda_function.py` file is formatted to run in AWS. This file should be updated for any changes related to the AWS zoom-bot instance.

When updating the app, make all changes and zip the enitre folder after. If adding any imports, add them locally via `pip install package_name -t .` when in the zoom-bot dir.

After updates, run `zip -r ../zoom-bot.zip .` and in AWS chose to edit code via uploading a zip file.

Alternatively, you can make changes in the AWS Lambda GUI, reflecting them in the repo after.

## Local Installation

```
brew install python3
pip install jsonschema
```
*Note: Packages need to be for Python 3, not Python 2

## Usage

```python3 zoom-bot.py config_file```

e.g. ```python3 zoom-bot.py test.json```

## Options
See `config.schema` for details.

The config file is hosted in the `zoom-bot-config` S3 bucket. Make changes by pulling down the file, editing, and uploading:

```
aws s3 cp s3://zoom-bot-config/config.json .
aws s3 cp config.json s3://zoom-bot-config/config.json
```


Where:
`zoomdayoffset` is the number of days before today to search for meetings. Useful if testing when a meeting has not occured yet on the day of testing. If multiple matching meetings are found, the newest is returned.

Other things in the config schema include:
- Zoom username of the meeting owner to search for recordings
- Name of meeting to search for (Must match Google Calendar meeting name)
- Name of users to tag in slack message
- Title of slack message (whatever you like to be displayed in the Slack alert)
- JWT for zoom- if expired, update on the [Zoom App portal](https://marketplace.zoom.us/user/build) (must be Zoom admin)
- Destination slack channel is set by the incoming webhook configured on the [Slack App portal](https://api.slack.com/apps)

...

### Bugs

...

## License
© Parkside Technologies, Inc.
