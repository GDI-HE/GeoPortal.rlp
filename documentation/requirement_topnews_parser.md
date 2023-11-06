# MediaWiki News Documentation

This repository contains documentation on creating news articles in MediaWiki, with a focus on using the `topNews` template.

## Introduction

The `topNews` template is designed for creating news articles in MediaWiki. It's particularly useful for highlighting important news or announcements at the top of a page.

## How to Use the `topNews` Template  

To create a news article using the `topNews` template, follow these steps:

### 1. Template Structure

Here's the structure of the `topNews` template:

```html
<div class="topNews">
  <h2 class="topNewsTitle">{{{title|}}}</h2>
  <span class="topNewsDate"><strong>{{{date|}}}</strong></span>
  <span class="hiddenDuration" style="display:none;">{{{durationDays|}}}</span>
  <p class="teaser">{{{teaser|}}}</p>
  <p class="articleBody">{{{articleBody|}}}</p>
  
  {{#if: {{{link|}}} {{{text|}}} | 
    <span class="external text"><strong>[{{{link|}}} {{{text|}}}]</strong></span>
  }}
  {{#if: {{{email|}}} | 
    <span class="contact">Email: [mailto:{{{email|}}} {{{email|}}}]</span>
  }}
  <hr>
</div>
```
This template could be searched in our mediawiki using: `Vorlage:topNews`
The `<hr>` part could be removed and instead of using `<hr>` in the template, `----` could be used between the News. 
```plaintext
{{topNews
|title = GDI-DE Newsletter 10/2023 
...
...
}}

----

{{topNews
|title = Wartungsarbeiten Geobasisdaten wichtig
...
...
}}

----
```

### 2. Parameters

When using the `topNews` template, you can specify the following parameters:

● `title`: The title of the news article.

● `date`: The publication date in the format "dd.mm.yyyy."

● `durationDays` (optional): The number of days from the published day to the day of maintenance day, i.e. The duration between the publication date and the maintenance day. This will be hidden in the output.

● `teaser`: A brief teaser or summary of the news which will be displayed on the landing page.

● `articleBody`: The main content of the news article.

● `link` (optional): The URL link to the full news article.

● `text` (optional): The text to display for the link.

● `email` (optional): An email address for contact information.

### Using the `topNews` Template

You can use the `topNews` template to create news articles (Meldungen) in MediaWiki. Here's an example of how to use it:

```plaintext
{{topNews
|title = GDI-DE Newsletter 10/2023 
|date = 02.10.2023
|durationDays =5
|teaser = Der GDI-DE Newsletter Oktober 2023
|articleBody = Die Koordinierungsstelle GDI-DE möchte mit ihrem Newsletter über die aktuellen Entwicklungen in der GDI-DE unterrichten. Der GDI-DE Newsletter erscheint seit 2006 in regelmäßigen Abständen und informiert kurz und bündig über allen aktuellen Themen.
<div class="custom-link" style="display: block; margin: 0; padding: 0;">
  [[Datei:GDI_DE_LOGO.PNG|link=https://{{SERVERNAME}}/mediawiki/images/3/3d/GDI_DE_LOGO.PNG|rahmenlos|300px]]
</div>
|link = https://www.gdi-de.org/Service/Aktuelles/gdi-de-news-oktober-2023
|text = GDI Newsletter 10/2023
}} 

```

### Custom CSS Usage

In the edited news articles, you've applied custom CSS to ensure that images do not overlap the `articleBody` and are displayed as a block. Here's an example of how you've used custom CSS:

```html
<div class="custom-link" style="display: block; margin: 0; padding: 0;">
  [[Datei:GDI_DE_LOGO.PNG|link=https://{{SERVERNAME}}/mediawiki/images/3/3d/GDI_DE_LOGO.PNG|rahmenlos|300px]]
</div>
```
The following problem will be solved: 
![grafik](https://github.com/dpakprajul/landing_page/assets/38970123/d4d98389-be60-463c-b2bb-17b35288d45d)


By introducing a new div with "display:block;" style, this problem is solved!

![grafik](https://github.com/dpakprajul/landing_page/assets/38970123/b3fee446-0ea0-489d-a688-0415376c6365)


### What If It's Not a topNews Article?

If the news article you're creating doesn't require the topNews format (or it's not a topNews), consider using the standard MediaWiki syntax for articles. If you're unsure, reach out to the documentation maintainers for guidance. A new template for non-topNews will also be worked out soon.

### Custom Text Inside `topNews`

You can add various types of text and content within the `topNews` template to provide additional information or context to your news articles. But be sure it looks okay in the test site. Here's an example of how to include custom text:

```plaintext
{{topNews
|title = GDI-DE Newsletter 10/2023 
|date = 02.10.2023
|durationDays =5
|teaser = Der GDI-DE Newsletter Oktober 2023
|articleBody = Die Koordinierungsstelle GDI-DE möchte mit ihrem Newsletter über die aktuellen Entwicklungen in der GDI-DE unterrichten. Der GDI-DE Newsletter erscheint seit 2006 in regelmäßigen Abständen und informiert kurz und bündig über allen aktuellen Themen.
<div class="custom-link" style="display: block; margin: 0; padding: 0;">
  [[Datei:GDI_DE_LOGO.PNG|link=https://{{SERVERNAME}}/mediawiki/images/3/3d/GDI_DE_LOGO.PNG|rahmenlos|300px]]
</div>
* Die Datenbasis ist tagesaktuell (ATKIS® Basis-DLM Daten).
* Die Prozessierung der Karte erfolgt automatisiert und täglich.
* Die Gestaltung und der Inhalt der Karte orientieren sich an den Karten aus dem Saarland und Rheinland Pfalz.
* Die Prozessierung und Bereitstellung erfolgt vollständig mit OpenSource Software (PostNAS Projekt).
|link = https://www.gdi-de.org/Service/Aktuelles/gdi-de-news-oktober-2023
|text = GDI Newsletter 10/2023
}} 
```
### What if the author forgot to write the date, title or any other part?
An approach to create an extention for the validation was done on mediawiki page but the attempt was unsuccessful.
For the topNews to be in priority, the created date and the duration is of prime importance. If the current date is not given, the function cannot run and results error, hence was blocked with Exception error and handled it accordingly. 

#### TODO
Create an extension for the validation in mediawiki page. (Using php and making change in LocalSettings.php and adding a new extensions called Validation inside the folder extentions. The extensions will be usually inside usr/share/mediawiki/extensions/Validation
Created a extension.json and Validation.php inside it but have to work further to make it run. The script I had used is in Issues in this repo.

The result looks like: 
![grafik](https://github.com/dpakprajul/landing_page/assets/38970123/481b1e5c-9b45-4cea-8e96-8493b3368d92)


If you have any questions and problems regarding the template and page editing, please write me an email: [Deepak.Parajuli@hvbg.hessen.de]
