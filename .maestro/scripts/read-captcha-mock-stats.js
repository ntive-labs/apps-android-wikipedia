// Reads the CAPTCHA mock's bookkeeping (GET /mock/stats, see
// .maestro/mock/captcha_login_server.py) and flattens it into `output.*` values that a flow
// can assert on with `assertTrue`.
//
// This is how a flow checks what the *server* was actually asked for - which requests
// arrived, in which order, and what bytes went back - as opposed to what the screen shows.
//
// env:
//   MOCK_STATS_URL  the /mock/stats endpoint as seen from the host running maestro
//                   (e.g. http://localhost:8080/mock/stats). Note this is NOT the URL the
//                   app uses: the emulator reaches the same server through 10.0.2.2.

var statsUrl = typeof MOCK_STATS_URL !== 'undefined' ? MOCK_STATS_URL : env.MOCK_STATS_URL;

var response = http.get(statsUrl);
if (!response.ok) {
    throw new Error('CAPTCHA mock did not answer ' + statsUrl + ' (HTTP ' + response.status + ')');
}

var stats = json(response.body);
var images = stats.captcha_image_requests;

// How many replacement challenges were asked for, i.e. action=fancycaptchareload calls.
output.captchaReloadRequests = stats.captcha_reload_requests;

// Every Special:Captcha/image GET since this login attempt started, in arrival order.
output.captchaImageRequests = images.length;

var replacements = 0;
for (var i = 0; i < images.length; i++) {
    if (images[i].isReload) {
        replacements++;
    }
}
output.replacementImageRequests = replacements;

var blank = { captchaId: '', sha256: '', word: '', isReload: false };
var first = images.length > 0 ? images[0] : blank;
var last = images.length > 0 ? images[images.length - 1] : blank;

// The challenge the app displayed first...
output.firstImageId = first.captchaId;
output.firstImageSha = first.sha256;
output.firstImageWord = first.word;

// ...and the one it is displaying now. Different id + different SHA-256 means the bytes
// handed to the CAPTCHA ImageView really are a different image.
output.lastImageId = last.captchaId;
output.lastImageSha = last.sha256;
output.lastImageWord = last.word;
output.lastImageIsReplacement = last.isReload;
