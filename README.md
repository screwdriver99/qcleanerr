Code forked from [sonarr-radarr-queue-cleaner](https://github.com/MattDGTL/sonarr-radarr-queue-cleaner).

This fork is just a simplified version of the MattDGTL repo

## Requisites

- Docker
- Python 3.9 or higher

## Getting Started

1. Clone this repository to your local machine
2. Edit the Dockerfile inserting the correct URLs and api keys. One of the URL may remain blank
3. Create the image with `sudo docker build . -t docker/qcleanerr` (you may choose the name you like)

## How it works

Once every 10 minutes the script connects to the download service (Radarr|Sonarr) and gets the list of running downloads. 
Then, it checks which of them is in a failure state and tracks all of them.
When a download entry stays in failure state for more than one hour (this can be set in the code, may become a parameter in the future), 
it's removed from the download client and blacklisted, so the service will not re-add it anymore.

The failure-check criteria is customizable in the function `isFailed(record)`. See the [/api/v3/queue](https://radarr.video/docs/api/#/Queue/get_api_v3_queue).
Note: the 'record' object is passed to this function.

## Contributing

Feel free to suggest improvements and contribute to the project
