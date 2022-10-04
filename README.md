# Scraper for start.me pages

Run to scrape all links and text from a public user-posted page.

# Running

    1.  Clone this repository using `git`

    2.  (Optional) Activate a virtual environment

        This will keep the installed packages separate from any previous installations on your system

        On windows:
            `python -m venv venv && venv\Scripts\activate`

        On mac/linux:
            `python3 -m venv venv && source venv/bin/activate`

        Note: If you choose to use a venv you must activate it every time before you run this script (run the part after the `&&`)


    3.  Install requirements

        Install the latest versions of the required packages (will most likely work):

        `pip install -U requests click` 
        Note: on mac/linux use `pip3` instead of `pip`.

        If you ran the above but the script fails then try to install these specific versions:

        ```
        Package            Version
        ------------------ -----------
        Brotli             1.0.9
        click              8.1.3
        requests           2.28.1
        ```

        If it still fails then please open an issue and I will try to look into it.

    4.  Executing

        On windows:

            `python main.py ...`

        On mac/linux:

            `python3 main.py ...`

            If you want to just run it without typing "python" then the command `chmod +x main.py`
            is what you are looking for. Afterwards you can just type `./main.py`

# Command line arguments

You can use `python main.py --help` for more help.

* `-o`, `--out` `[PATH]` Output file
* `-p`, `--pretty` Enable pretty-printing of JSON output
* `--no-pretty` Explicitly disable pretty-printing (does nothing for CSV format)
* `-k`, `--keep-temp` Save raw responses from server
* `-f`, `--format` Pick format of output. Allowed: CSV, JSON, XML.

# Example usage

Save as pretty JSON to default file 'xxxxxx-DATE.json'

`python main.py https://start.me/p/xxxxxx/some-title`

Save as compact XML to the file 'saved.xml'

`python main.py https://start.me/p/xxxxxx/some-title --no-pretty -f xml -o saved.xml`

Save as CSV to default file 'xxxxxx-DATE.csv'

`python main.py https://start.me/p/xxxxxx/some-title -f csv`
