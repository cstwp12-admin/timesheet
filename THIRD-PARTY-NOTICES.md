# Third-party notices

Timesheet includes the following open-source components, unchanged, so that it works offline. Each keeps its own licence. None of them is "copyleft" as used here: they allow use in an app under any licence, provided these notices are kept.

| Component | File(s) | Licence | Copyright |
|---|---|---|---|
| jsPDF 2.5.1 | `lib/jspdf.umd.min.js` | MIT | © 2010–2021 James Hall, yWorks GmbH and contributors |
| JSZip 3.10.1 (includes pako) | `lib/jszip.min.js` | MIT or GPLv3, **used under MIT**; pako: MIT and Zlib | © 2009–2016 Stuart Knightley, David Duponchel, Franz Buchinger, António Afonso; pako © 2014–2017 Vitaly Puzrin and Andrey Tupitsin |
| pdf-lib | `lib/pdf-lib.min.js` | MIT (includes tslib, © Microsoft, 0BSD header) | © 2019 Andrew Dillon |
| PDF.js 3.11.174 | `lib/pdfjs.min.js`, `lib/pdfjs.worker.min.js` | Apache License 2.0 | © Mozilla Foundation |
| QR Code Generator for JavaScript | `lib/qrcode.min.js` | MIT | © 2009 Kazuhiko Arase |
| jsQR | `lib/jsQR.min.js` | Apache License 2.0 | © Cosmo Wolfe and contributors |
| Tesseract.js 5.1.1, tesseract.js-core | `lib/tesseract/*.js` | Apache License 2.0 (see `lib/tesseract/LICENSE-tesseract.js.md`) | © Jerome Wu and contributors; Tesseract OCR © Google and contributors |
| Tesseract English language data | `lib/tesseract/lang/eng.traineddata.gz` | Apache License 2.0 | © Google and contributors |

**Typefaces.** The app and the docs website load Barlow, Barlow Condensed and IBM Plex Mono from Google Fonts (SIL Open Font License 1.1). They are not stored in this repository.

The rest of the app and the docs theme are original work by WPN (see [LICENSE.md](LICENSE.md)).

## MIT licence (jsPDF, JSZip, pdf-lib, QR Code Generator)

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Apache License 2.0 (PDF.js, jsQR, Tesseract.js and its language data)

The full text is in `lib/tesseract/LICENSE-tesseract.js.md` and at https://www.apache.org/licenses/LICENSE-2.0. The files are used unmodified.
