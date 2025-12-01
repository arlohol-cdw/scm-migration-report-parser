# scm-migration-report-parser
Script to parse the JSON configuration compatibility report from the NGFW to Strata Cloud Manager Migration process.

# Usage
There are two options. If you have the Panorama XML, you can render the XML sections that are referenced in the report, but you can run this without.
Option 1:
```
python scm-migration-parser.py <input.json> [output.html]
```

Option 2:
```
python scm-migration-parser.py <input.json> [output.html] --xml [panorama-config.xml]
```
