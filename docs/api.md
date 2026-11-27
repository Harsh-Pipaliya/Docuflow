# HTTP API

GET /api/auth/me returns authentication state and the CSRF token, creating an anonymous session if necessary. POST /api/auth/login takes username and password. POST /api/auth/logout ends the session. All writes require the X-CSRF-Token header.

POST /api/documents accepts one multipart field named file. A 201 response includes file_id. GET /api/documents lists documents; GET /api/stats counts them by state. GET /api/documents/{id} returns metadata and GET /api/documents/{id}/history returns ordered transitions. GET /api/documents/{id}/download streams the original. DELETE /api/documents/{id} removes a terminal document. POST /api/documents/{id}/reprocess starts a new attempt on a failed object.

GET /api/integrations returns evidence classifications. GET /healthz is public. Server errors return an error object containing a numeric HTTP code and a user-facing message.
