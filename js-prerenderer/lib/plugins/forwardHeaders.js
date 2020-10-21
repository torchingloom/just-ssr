module.exports = function (keys) {
    return {
        tabCreated: (req, res, next) => {

            if ((!keys || !keys.length) && process.env.FORWARD_HEADER) {
                keys = process.env.FORWARD_HEADER.split(',') || [];
            }
            var customHeaders = {}
            for (var i = 0; i < keys.length; i++) {
                if (req.headers[keys[i]] || req.headers[keys[i].toLowerCase()]) {
                    customHeaders[keys[i]] = (req.headers[keys[i]]) ? req.headers[keys[i]] : req.headers[keys[i].toLowerCase()];
                }
            }

            req.prerender.tab.Network.setExtraHTTPHeaders({
                headers: customHeaders
            });

            next();
        }
    }
}