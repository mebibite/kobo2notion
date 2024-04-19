# kobo2notion

For avid readers who use Kobo e-readers and Notion, kobo2notion automates the process of syncing your reading insights with your Notion workspace. By seamlessly transferring your Kobo highlights, annotations and bookmarks to Notion pages it allows for efficient organization, enrichment and retrieval of your reading notes.

## Installation
1. kobo2notion requires the python3 and python3-pip packages to be installed.

2. Install the required Python packages using pip3:
```bash
pip3 install -r requirements.txt
```

## Configuration

1. Verify that the 'kobo/database_path' setting in the config.yaml file matches the location of the 'KoboReader.sqlite' on your Kobo e-reader when connected.

2. Optionally, change the location where the database will be cached on the local file system in the 'kobo/database_cache' setting in the config.yaml file.

3. Create a new integration at [Notion Integrations](https://www.notion.so/my-integrations), selecting the target workspace.

4. Name the integration 'kobo2notion' and submit. Copy the 'Internal Integration Secret' contents.

5. Paste the secret into the 'notion/integration_token' setting in the config.yaml file.

6. Navigate to the target Notion workspace in your browser via [Notion](https://www.notion.so/) and select the folder where kobo2notion will create pages. Click on the '...' icon in the upper right corner, go to the 'Connect to' menu item, and select 'kobo2notion'. Click the 'Confirm' button.

7. In your browser's URL bar, you see a URL in the following format: `https://www.notion.so/{name}-{id}`. Copy the `{id}` part of the URL. For example, in the case of `https://www.notion.so/example-36ec47c6b3084bd484352720d0e03562`, you would need to copy `36ec47c6b3084bd484352720d0e03562`.

8. Paste the page's ID into the 'notion/parent_page' setting in the config.yaml file.

9. Optionally, configure a different icon for the Notion pages that kobo2notion will create via the 'notion/icon' setting in the config.yaml file. By default, the icon will be an opened book.

10. Optionally, the 'kobo2notion/delta_date' setting in the config.yaml file allows you to specify a delta date. If specified, only Kobo highlights, annotations, and bookmarks created or updated after that date and time will be exported to Notion. The format for this setting is 'YYYY-MM-DD HH:MM:SS'. It will be automatically updated by the application after each successful run.

## Execute

Connect your Kobo e-reader and run the 'kobo2notion.py' Python script.