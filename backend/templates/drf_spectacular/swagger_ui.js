const microblendSwaggerSettings = {{ settings|safe }} || {};
const microblendOAuth2Config = {{ oauth2_config|safe }} || {};

function microblendReadCsrfToken() {
  const cookie = document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="));
  return cookie ? decodeURIComponent(cookie.split("=")[1]) : null;
}

const microblendUi = SwaggerUIBundle(
  Object.assign(
    {
      url: "{{ schema_url|escapejs }}",
      dom_id: "#swagger-ui",
      presets: [
        SwaggerUIBundle.presets.apis,
        SwaggerUIStandalonePreset,
      ],
      layout: "StandaloneLayout",
      requestInterceptor: (request) => {
        const method = (request.method || "get").toLowerCase();
        if (["post", "put", "patch", "delete"].includes(method)) {
          const csrfToken = microblendReadCsrfToken();
          if (csrfToken) {
            request.headers["{{ csrf_header_name|escapejs }}"] = csrfToken;
          }
        }
        return request;
      },
    },
    microblendSwaggerSettings,
  ),
);

if (Object.keys(microblendOAuth2Config).length > 0) {
  microblendUi.initOAuth(microblendOAuth2Config);
}

window.ui = microblendUi;
