# gcal copier

---

## What's this?
- To copy one calendar events to another calendar in Google calendar.
- You have to:
  - specify copy source calendar id
  - specify copy dest calendar id
- This tool will copy all of the events from source to dest including color information, which you cannot do by manual export and import using ical

## How to use
1. create GCP account. Ref: https://www.jicoo.com/magazine/blog/google-calendar-api
2. Get GCP auth information
   1. Service account or OAuth2.0
      1. https://qiita.com/doran/items/c735c7b05c0a2ed4bfdb
      2. https://zenn.dev/nomhiro/articles/google-calendar-api
   2. This code is using OAuth2.0
3. Put crenditals.json under project root in your local
4. `$ uv run copier.py`
