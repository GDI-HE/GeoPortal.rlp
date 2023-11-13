# MediaWiki News Documentation

This repository contains documentation on creating news articles in MediaWiki, with a focus on using the `topNews` template.

## Introduction

The `topNews` template is designed for creating news articles in MediaWiki. It's particularly useful for highlighting important news or announcements at the top of the landing page.

## How to Use the `topNews` Template  

To create a news article using the `topNews` template, follow these steps:

### 1. Create the template inside mediawiki

It can be created or viewed if it exist. Search inside mediawiki searchfield using: `Vorlage:topNews`

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
The `<hr>` part is not necessary and could be ignored. 


### 2. Parameters

When using the `topNews` template, following parameters are available:

- `title`: The title of the news article.

- `date`: The publication date in the format "dd.mm.yyyy."

- `durationDays` (optional): The number of days from the published day to the day of maintenance day, i.e. The duration between the publication date and the maintenance day. This will be hidden in the output.

- `teaser`: A brief teaser or summary of the news which will be displayed on the landing page.

- `articleBody`: The main content of the news article.

- `link` (optional): The URL link to the full news article.

- `text` (optional): The text to display for the link.

- `email` (optional): An email address for contact information.

### Using the `topNews` Template in the Meldungen article

Here's an example of how to use it - the position in the article doesn’t matter:

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

In the edited news articles, you can apply custom CSS to ensure that e.g. images are placed in a new line. Here's an example:

```html
<div class="custom-link" style="display: block; margin: 0; padding: 0;">
  [[Datei:GDI_DE_LOGO.PNG|link=https://{{SERVERNAME}}/mediawiki/images/3/3d/GDI_DE_LOGO.PNG|rahmenlos|300px]]
</div>
```

### What If It's Not a topNews Article?

If the news article you're creating doesn't require the topNews format (or it's not a topNews), keep using the standard MediaWiki syntax for articles.

### Custom Text Inside `topNews`

You can add various types of text and content within the `topNews` articleBody parameter to provide additional information or context to your topNews articles. But be sure it looks okay in the test site. Here's an example of how to include custom text:

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
### error handling due to missing mandatory parameters
What if the author forgot to write the date, title or any other mandatory part?
For the topNews to be in priority, the created date and the duration is of prime importance. If the current date is not given, the function cannot run and results error, hence was blocked with Exception error and handled it accordingly. 

### Possible Extension
Create an extension for the validation in mediawiki page before save. 



If you have any questions and problems regarding the template and page editing, please write me an email: [Deepak.Parajuli@hvbg.hessen.de]
