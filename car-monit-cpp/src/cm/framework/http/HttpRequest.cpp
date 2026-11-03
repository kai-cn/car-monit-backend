#include "cm/framework/http/HttpRequest.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>

#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/StringUtils.hpp"

namespace cm::http {

namespace {
std::string lower(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}
int hexVal(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}
} // namespace

std::string HttpRequest::percentDecode(const std::string& s, bool plusAsSpace) {
    std::string out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        char c = s[i];
        if (c == '+' && plusAsSpace) {
            out.push_back(' ');
        } else if (c == '%' && i + 2 < s.size()) {
            int hi = hexVal(s[i + 1]);
            int lo = hexVal(s[i + 2]);
            if (hi >= 0 && lo >= 0) {
                out.push_back(static_cast<char>(hi * 16 + lo));
                i += 2;
            } else {
                out.push_back(c);
            }
        } else {
            out.push_back(c);
        }
    }
    return out;
}

/** application/x-www-form-urlencoded 语义：+ 表示空格 */
std::string HttpRequest::urlDecode(const std::string& s) { return percentDecode(s, true); }

std::string HttpRequest::urlEncode(const std::string& s) {
    static const char* hex = "0123456789ABCDEF";
    std::string out;
    for (unsigned char c : s) {
        if (std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            out.push_back(static_cast<char>(c));
        } else if (c == ' ') {
            out.push_back('+');
        } else {
            out.push_back('%');
            out.push_back(hex[c >> 4]);
            out.push_back(hex[c & 0xF]);
        }
    }
    return out;
}

void HttpRequest::parseUrlEncoded(const std::string& text,
                                  std::vector<std::pair<std::string, std::string>>& out) {
    size_t start = 0;
    while (start <= text.size()) {
        size_t amp = text.find('&', start);
        std::string pair = text.substr(start, amp == std::string::npos ? std::string::npos : amp - start);
        if (!pair.empty()) {
            auto eq = pair.find('=');
            if (eq == std::string::npos) {
                out.emplace_back(urlDecode(pair), "");
            } else {
                out.emplace_back(urlDecode(pair.substr(0, eq)), urlDecode(pair.substr(eq + 1)));
            }
        }
        if (amp == std::string::npos) break;
        start = amp + 1;
    }
}

void HttpRequest::parseCookies(const std::string& header,
                               std::vector<std::pair<std::string, std::string>>& out) {
    size_t start = 0;
    while (start <= header.size()) {
        size_t semi = header.find(';', start);
        std::string pair = utils::StringUtils::trim(
            header.substr(start, semi == std::string::npos ? std::string::npos : semi - start));
        if (!pair.empty()) {
            auto eq = pair.find('=');
            if (eq != std::string::npos) out.emplace_back(pair.substr(0, eq), pair.substr(eq + 1));
        }
        if (semi == std::string::npos) break;
        start = semi + 1;
    }
}

std::vector<MultipartPart> HttpRequest::parseMultipart(const std::string& body,
                                                       const std::string& content_type) {
    std::vector<MultipartPart> parts;
    std::string boundary;
    auto pos = content_type.find("boundary=");
    if (pos != std::string::npos) {
        boundary = content_type.substr(pos + 9);
        if (!boundary.empty() && boundary.front() == '"') {
            auto end = boundary.find('"', 1);
            boundary = boundary.substr(1, end == std::string::npos ? std::string::npos : end - 1);
        }
        auto semi = boundary.find(';');
        if (semi != std::string::npos) boundary = boundary.substr(0, semi);
    }
    if (boundary.empty()) return parts;

    const std::string delim = "--" + boundary;
    size_t start = body.find(delim);
    if (start == std::string::npos) return parts;
    start += delim.size();

    while (true) {
        if (body.compare(start, 2, "--") == 0) break;
        if (body.compare(start, 2, "\r\n") == 0) start += 2;
        size_t header_end = body.find("\r\n\r\n", start);
        if (header_end == std::string::npos) break;
        std::string raw_headers = body.substr(start, header_end - start);
        size_t data_start = header_end + 4;
        size_t next = body.find("\r\n" + delim, data_start);
        if (next == std::string::npos) next = body.size();
        MultipartPart part;
        part.data = body.substr(data_start, next - data_start);

        std::istringstream hs(raw_headers);
        std::string line;
        while (std::getline(hs, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            auto colon = line.find(':');
            if (colon == std::string::npos) continue;
            std::string key = lower(utils::StringUtils::trim(line.substr(0, colon)));
            std::string value = utils::StringUtils::trim(line.substr(colon + 1));
            part.headers[key] = value;
            if (key == "content-type") part.content_type = value;
            if (key == "content-disposition") {
                auto npos = value.find("name=\"");
                if (npos != std::string::npos) {
                    auto q = value.find('"', npos + 6);
                    part.name = value.substr(npos + 6, q == std::string::npos ? q : q - npos - 6);
                }
                auto fpos = value.find("filename=\"");
                if (fpos != std::string::npos) {
                    auto q = value.find('"', fpos + 10);
                    part.filename = value.substr(fpos + 10, q == std::string::npos ? q : q - fpos - 10);
                }
            }
        }
        parts.push_back(std::move(part));
        if (next >= body.size()) break;
        start = next + 2 + delim.size();
    }
    return parts;
}

std::string HttpRequest::getHeader(const std::string& name) const {
    auto it = headers.find(lower(name));
    return it == headers.end() ? "" : it->second;
}

std::optional<std::string> HttpRequest::getParameter(const std::string& name) const {
    for (const auto& [k, v] : form_params) if (k == name) return v;
    for (const auto& [k, v] : query_params) if (k == name) return v;
    for (const auto& p : parts) if (p.name == name) return p.data;
    return std::nullopt;
}

std::vector<std::string> HttpRequest::getParameterValues(const std::string& name) const {
    std::vector<std::string> out;
    for (const auto& [k, v] : form_params) if (k == name) out.push_back(v);
    for (const auto& [k, v] : query_params) if (k == name) out.push_back(v);
    return out;
}

bool HttpRequest::hasParameter(const std::string& name) const {
    return getParameter(name).has_value();
}

std::string HttpRequest::getParameterOr(const std::string& name, const std::string& def) const {
    auto v = getParameter(name);
    return v ? *v : def;
}

std::optional<std::string> HttpRequest::getCookie(const std::string& name) const {
    for (const auto& [k, v] : cookies) if (k == name) return v;
    return std::nullopt;
}

bool HttpRequest::isMultipart() const {
    return lower(contentType()).find("multipart/form-data") != std::string::npos;
}

std::optional<MultipartPart> HttpRequest::getPart(const std::string& name) const {
    for (const auto& p : parts) if (p.name == name) return p;
    return std::nullopt;
}

std::string HttpRequest::getSessionId() const {
    auto c = getCookie("JSESSIONID");
    return c.value_or("");
}

Json HttpRequest::json() const {
    if (body.empty()) {
        // Java: Required request body is missing
        throw exception::JsonParseException(
            "Required request body is missing");
    }
    return parse_json(body);
}

} // namespace cm::http
