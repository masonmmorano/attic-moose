# Attic Moose 🦌📚

A simple tool to help you find the right people to review your children's book —
librarians, teachers, book bloggers, therapists, child psychologists, homeschool
groups, and children's-book influencers — and to write personalized outreach
emails to them.

**It does this the legitimate way:** it only looks at *public* pages that are
meant for contact (review policies, staff directories, association contact pages,
public business emails). It respects each site's rules (`robots.txt`), goes
slowly so it's a polite web citizen, and **never sends anything on its own** —
you review every email before it goes out.

> It does **not** scrape Instagram or Facebook behind logins, and it does **not**
> mass-blast emails. Those get you banned and marked as spam. This tool is built
> to keep your name, your accounts, and your sender reputation safe.

---

## What you'll do, start to finish

1. Install Python (one time).
2. Install the tool's helpers (one command).
3. Get a free search key and paste it into a settings file.
4. Run **discover** to build a list of contacts.
5. **Look at the list** and remove anyone who doesn't fit.
6. Run **draft** to create personalized emails.
7. Open the drafts, read them, and send the ones you like.

Take it one step at a time — the commands are copy-paste.

---

## Step 1 — Install Python (one time)

If you don't already have Python 3.10+:

- **Windows:** download it from <https://www.python.org/downloads/> and, during
  install, **check the box that says "Add Python to PATH."**

To confirm it worked, open **PowerShell** (search for it in the Start menu) and type:

```powershell
python --version
```

You should see something like `Python 3.12.0`.

---

## Step 2 — Set up the tool (one time)

In PowerShell, go to this folder. If you downloaded it to your Documents:

```powershell
cd "$HOME\Documents\repositories\attic-moose"
```

Then create a private workspace and install the helpers:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

After this, your prompt will start with `(.venv)`. That's good — it means the
tool's helpers are ready.

> Next time you come back, you only need to repeat the `cd ...` line and the
> `.\.venv\Scripts\Activate.ps1` line. Not the install.

---

## Step 3 — Get a free search key (one time, ~3 minutes)

The tool searches the web using **Brave Search**, which has a free tier.

1. Go to <https://brave.com/search/api/> and click to sign up.
2. Choose the **Free** plan.
3. Copy your **API key** (a long string of letters and numbers).

Now make your settings file:

```powershell
Copy-Item config.example.yaml config.yaml
notepad config.yaml
```

In the file that opens, fill in:

- Your **book** title, author name, link (your Amazon page), and a short blurb.
- Your **reply_to** email and a real **mailing_address**
  (this is legally required on outreach emails — a PO box is fine).
- Paste your Brave key into **brave_api_key**.
- Leave the `audiences` list as-is to target everyone, or delete lines you don't want.
- Optionally add cities/regions under `regions` to make results more local.

Save and close Notepad. (Your `config.yaml` stays private — it's never shared.)

---

## Step 4 — Discover contacts

```powershell
python -m attic_moose discover
```

You'll see it run searches and print each contact it finds. When it's done, it
writes everything to **`output\contacts.csv`**.

> **Tip:** the first time, try a small test run so you don't use up searches:
> `python -m attic_moose discover --limit 3`

---

## Step 5 — Review the list (important!)

Open `output\contacts.csv` (double-click — it opens in Excel or similar).

Each row shows the email, who/what it is, the audience, and **the web page it
came from**. Spend a few minutes here:

- Delete anyone who clearly doesn't fit.
- The `source_url` column lets you double-check a contact is really relevant.

Quality beats quantity — a short list of *right* people gets far more reviews
than a big list of random ones.

---

## Step 6 — Create personalized email drafts

```powershell
python -m attic_moose draft
```

This creates one email per contact in **`output\drafts\`**, each personalized and
matched to the audience (a librarian gets a different message than a blogger).
Every email includes an unsubscribe line and your address, as the law requires.

Open any `.eml` file to read it. Edit the wording in the `templates\` folder if
you want to change the messages, then run `draft` again.

---

## Step 7 — Send

Open each draft in your email program, give it a final read, and send the ones
you like. **You're in control of every send.**

If someone replies "unsubscribe" (or asks you to stop), record it so they're
never contacted again:

```powershell
python -m attic_moose suppress someone@example.com
```

---

## Doing it again for book 2 and 3

When your next book is out, just update the `book:` section in `config.yaml` and
run `discover` and `draft` again. The tool remembers who you've already found and
won't create duplicates.

---

## Sending automatically through Gmail (optional, later)

By default the tool makes drafts and you send them — the safest approach. If you
later want it to create drafts directly in your Gmail, see the instructions at
the top of `attic_moose\gmail.py`, then run:

```powershell
python -m attic_moose draft --gmail-drafts
```

It's set up to create **drafts only** (it can't send on its own) so there's no
way to accidentally blast emails.

---

## Command reference

| Command | What it does |
|---|---|
| `python -m attic_moose discover` | Search the web and collect contacts |
| `python -m attic_moose discover --limit 3` | Same, but only the first 3 searches (testing) |
| `python -m attic_moose list` | Show a summary of what's collected |
| `python -m attic_moose list --export` | Re-export the CSV |
| `python -m attic_moose draft` | Create personalized email drafts |
| `python -m attic_moose suppress EMAIL` | Add someone to the do-not-contact list |

---

## Playing fair (and why it helps you)

This tool deliberately:

- only reads **public, contact-intended** pages, and obeys each site's `robots.txt`;
- waits between requests so it never hammers a website;
- stores the **source** of every contact so you can verify it;
- keeps a **do-not-contact** list and puts an **unsubscribe + your address** in
  every email (required by the US CAN-SPAM Act);
- makes **drafts**, not automatic sends.

These aren't just rules — they're what keeps your emails out of spam folders and
gets your book actually read. A polite, personal note to the right person works.
A bulk blast doesn't.

> A note on Instagram/Facebook: there's no compliant way to bulk-DM strangers on
> those platforms, so this tool doesn't try. The legitimate path is the public
> **business email** a creator lists for contact — which the `influencer`
> audience targets.
