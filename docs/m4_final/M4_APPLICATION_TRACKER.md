# M4.1 — Application Tracking & Management

## 1. Overview

The Application Tracking & Management module provides a persistent way for students to record, update, search, monitor, and manage internship/job applications within the AI Career Companion Agent.

The module is implemented using **FastAPI REST APIs** backed by the project's **SQLite database**. Application records are associated with a candidate profile and can contain job information, application status, deadlines, interview information, notes, follow-up dates, and generated application documents.

The tracker is designed to connect the outputs of the career companion workflow with the student's real application-management process.

---

## 2. Objectives

The Application Tracker addresses the following requirements:

- Store internship/job application records.
- Associate applications with a student profile.
- Record company and job information.
- Track application dates and deadlines.
- Track application progress through predefined status stages.
- Record interview dates and interview status.
- Store notes and follow-up dates.
- Store customized resume and cover-letter outputs.
- Search and filter applications.
- Identify upcoming and overdue deadlines.
- Display application dashboard metrics.
- Show upcoming interviews and applications requiring follow-up.
- Prevent duplicate applications for the same profile and job ID.
- Support editing and deletion of application records.

---

## 3. Application Data Model

Applications are stored in the SQLite `applications` table.

### Core fields

| Field               | Description                                          |
| ------------------- | ---------------------------------------------------- |
| `id`                | Unique application identifier                        |
| `profile_id`        | Candidate profile associated with the application    |
| `job_id`            | Optional identifier of the related job               |
| `company_name`      | Company/organization name                            |
| `job_title`         | Position title                                       |
| `job_description`   | Optional job description                             |
| `application_date`  | Date on which the application was recorded/submitted |
| `deadline`          | Optional application deadline                        |
| `status`            | Current application stage                            |
| `interview_date`    | Optional interview date                              |
| `interview_status`  | Optional interview status                            |
| `notes`             | Student notes                                        |
| `follow_up_date`    | Optional follow-up date                              |
| `customized_resume` | Stored customized resume output                      |
| `cover_letter`      | Stored cover-letter output                           |
| `created_at`        | Record creation timestamp                            |
| `updated_at`        | Last update timestamp                                |

The database also creates indexes for profile-based application retrieval and status filtering.

---

## 4. Application Status Workflow

The backend defines the following supported application statuses:

1. **Saved**
2. **Planning to apply**
3. **Applied**
4. **Application under review**
5. **Shortlisted**
6. **Interview scheduled**
7. **Interview completed**
8. **Offer received**
9. **Rejected**
10. **Withdrawn**

The API validates supplied status values against this list. Invalid status values return an HTTP 400 error rather than being stored.

This provides a consistent application lifecycle while still allowing the student to manually update the current stage.

---

## 5. Application Creation

### Endpoint

`POST /profiles/{profile_id}/applications`

The endpoint accepts the `ApplicationCreateInput` model.

Supported input information includes:

- `job_id`
- `company_name`
- `job_title`
- `job_description`
- `application_date`
- `deadline`
- `status`
- `interview_date`
- `interview_status`
- `notes`
- `follow_up_date`
- `customized_resume`
- `cover_letter`

If an application date is not supplied, the backend uses the current UTC date.

### Duplicate protection

When a `job_id` is supplied, the backend checks whether an application for the same job already exists for the same profile.

If a duplicate is detected, the API returns HTTP 400 with an explanatory error instead of creating another record.

This protection was also validated during M4 end-to-end testing.

---

## 6. Application Retrieval

### List applications

`GET /profiles/{profile_id}/applications`

The endpoint returns applications belonging to the requested profile.

The response contains:

```text
profile_id
count
applications
```

Applications are ordered using the most recently updated records first.

### Individual application

`GET /profiles/{profile_id}/applications/{application_id}`

This endpoint retrieves a single application belonging to the specified profile.

If the application does not exist for that profile, the API returns HTTP 404.

---

## 7. Search and Filtering

The application-list endpoint supports several query parameters.

### Company filtering

```text
?company=<company>
```

Company matching is case-insensitive and uses partial matching.

### Role filtering

```text
?role=<role>
```

Job-title matching is case-insensitive and supports partial matching.

### Status filtering

```text
?status=<status>
```

Applications can be filtered by their current lifecycle status.

### Application-date filtering

```text
?application_date=<date>
```

The backend performs prefix-based matching against the stored application date.

### General search

```text
?search=<text>
```

The search term is checked against:

- Company name
- Job title
- Job description
- Notes

This provides a simple text-based search across important application information.

---

## 8. Deadline Filtering

The application tracker supports deadline-oriented filtering through:

```text
?deadline_filter=upcoming
?deadline_filter=overdue
?deadline_filter=has_deadline
```

### Upcoming

Applications with a deadline on or after the current UTC date are included.

Applications whose status is:

- Rejected
- Withdrawn
- Offer received

are excluded from the dashboard's active upcoming-deadline count.

### Overdue

Applications whose deadline is before the current UTC date are considered overdue, except applications already marked:

- Rejected
- Withdrawn
- Offer received

### Has deadline

Returns applications that contain a deadline value.

---

## 9. Application Dashboard

### Endpoint

`GET /profiles/{profile_id}/applications/dashboard`

The dashboard calculates application-management metrics from the stored application records.

### Metrics

The API provides:

| Metric                  | Meaning                                                      |
| ----------------------- | ------------------------------------------------------------ |
| `total_applications`    | Total number of stored applications                          |
| `active_applications`   | Applications not marked Rejected or Withdrawn                |
| `upcoming_deadlines`    | Active applications with deadlines on/after the current date |
| `interviews_scheduled`  | Applications with scheduled interview information            |
| `offers_received`       | Applications with status `Offer received`                    |
| `rejected_applications` | Applications with status `Rejected`                          |

The dashboard also provides supporting lists.

### Dashboard lists

The response contains:

- **Upcoming deadlines** — up to five relevant applications.
- **Recent applications** — five most recently created records.
- **Upcoming interviews** — up to five upcoming interview records.
- **Needing follow-up** — up to five records identified for follow-up.

Upcoming deadline and interview lists are sorted chronologically.

---

## 10. Interview Tracking

Interview information is stored directly with the application record.

The tracker supports:

- `interview_date`
- `interview_status`

The dashboard uses interview-date information to identify upcoming interviews.

This allows interview preparation generated by the Interview Agent to remain connected to the corresponding tracked application.

---

## 11. Follow-Up Tracking

Applications can contain a:

```text
follow_up_date
```

This allows students to record when they intend to follow up on an application.

The dashboard also exposes a `needing_followup` list, allowing follow-up-related records to be surfaced alongside deadlines and interviews.

---

## 12. Generated Application Documents

The application record supports storage of:

- `customized_resume`
- `cover_letter`

These fields can contain structured generated outputs.

The backend serializes dictionary/list values before database storage and reconstructs them when application records are returned.

This provides persistence for generated application materials alongside the job application they were created for.

The actual generation is handled by the **Application Agent**, while the Application Tracker stores the resulting outputs with the application record.

---

## 13. Updating Applications

### Endpoint

`PUT /profiles/{profile_id}/applications/{application_id}`

The update endpoint supports modification of application information including:

- Company
- Job title
- Job description
- Application date
- Deadline
- Status
- Interview date
- Interview status
- Notes
- Follow-up date
- Customized resume
- Cover letter

Only fields supplied in the request are updated.

The `updated_at` timestamp is refreshed after a successful update.

If no update fields are supplied, the existing application record is returned unchanged.

---

## 14. Deleting Applications

### Endpoint

`DELETE /profiles/{profile_id}/applications/{application_id}`

The endpoint removes the specified application belonging to the profile.

A successful deletion returns a confirmation message and the application ID.

If the application cannot be found for the specified profile, HTTP 404 is returned.

---

## 15. Profile-Level Data Isolation

Application records contain a `profile_id`, and application queries use this identifier when retrieving, updating, or deleting records.

Where an authenticated user is available, the backend also calls the profile-access validation mechanism before performing application operations.

This prevents application records from being accessed through a different profile context.

---

## 16. Database Design

The application table is created using:

```text
applications
```

with the following primary relationship:

```text
profiles
    |
    | profile_id
    v
applications
```

Indexes are created for:

```text
idx_applications_profile
idx_applications_status
```

These indexes support common profile-level and status-based application queries.

The initialization logic also checks the existing application-table schema and adds supported columns when required, helping maintain compatibility with an existing local database.

---

## 17. Application Tracker API Summary

| Method | Endpoint                                               | Purpose                                 |
| ------ | ------------------------------------------------------ | --------------------------------------- |
| POST   | `/profiles/{profile_id}/applications`                  | Create application                      |
| GET    | `/profiles/{profile_id}/applications`                  | List/search/filter applications         |
| GET    | `/profiles/{profile_id}/applications/dashboard`        | Application dashboard metrics and lists |
| GET    | `/profiles/{profile_id}/applications/{application_id}` | Retrieve one application                |
| PUT    | `/profiles/{profile_id}/applications/{application_id}` | Update application                      |
| DELETE | `/profiles/{profile_id}/applications/{application_id}` | Delete application                      |

---

## 18. Integration With Other Agents

The Application Tracker is not an isolated feature. It connects with the broader AI Career Companion workflow.

```text
Student Profile
      |
      v
Resume Processing
      |
      v
RAG Job Retrieval
      |
      v
Job-Resume Matching
      |
      v
Skill Gap Analysis
      |
      +----------------------+
      |                      |
      v                      v
Resume Customization    Cover Letter
      |                      |
      +----------+-----------+
                 |
                 v
          Application Tracker
                 |
        +--------+--------+
        |        |        |
        v        v        v
     Status   Deadline  Interview
        |        |        |
        +--------+--------+
                 |
                 v
            Dashboard
```

This allows generated career-assistance outputs to be associated with an actual application-management record.

---

## 19. Error Handling

The tracker validates important inputs before database operations.

Examples include:

### Invalid status

An unsupported status results in HTTP 400.

### Duplicate job application

If the same `job_id` is already associated with the same profile, creation is rejected with HTTP 400.

### Missing profile

If the requested profile does not exist, the API returns HTTP 404.

### Missing application

Retrieval, update, and deletion operations return HTTP 404 when the application does not belong to the requested profile or does not exist.

---

## 20. M4 Validation

Application Tracker functionality was included in the M4 end-to-end test suite.

The M4 E2E workflow validates application-tracking behavior together with:

- Profile creation
- Resume upload
- Resume parsing
- RAG job retrieval
- Job-resume matching
- Skill-gap analysis
- Resume customization
- Interview preparation
- Career Assistant
- Application tracking
- Error and edge-case handling
- Multi-agent consistency

The completed M4 E2E execution achieved:

```text
Total Tests Executed : 80
PASS                 : 80
FAIL                 : 0
BLOCKED              : 0
```

The application-tracking section itself completed successfully with:

```text
Application Tracker : 16/16 PASS
```

The E2E test therefore provides functional validation of the tracker APIs and their integration into the complete student workflow.

---

## 21. Current Implementation Characteristics

The current implementation provides a persistent CRUD-based application tracker with search, filtering, dashboard aggregation, deadline identification, interview tracking, follow-up information, and generated-document storage.

The application status is controlled through a fixed set of lifecycle values, while other application information remains editable.

The implementation uses deterministic database operations rather than requiring an LLM for basic application-management functionality. This is appropriate because CRUD operations, filtering, status validation, and dashboard calculations do not require generative AI.

---

## 22. Limitations and Future Improvements

The current implementation can be extended in future versions.

Potential improvements include:

- Automated scheduled notifications for deadlines.
- Automated interview reminders.
- Automated follow-up reminders.
- Calendar integration.
- Rich interview outcome tracking.
- Application analytics over time.
- Status-transition history/audit logs.
- Bulk application import.
- Sorting by arbitrary fields from the API.
- More advanced date-range filtering.
- Dedicated document version history.
- Automatic synchronization between generated documents and application records.
- Frontend-specific application-management views.

These are future enhancements rather than claims about the current implementation.

---

## 23. Conclusion

The M4.1 Application Tracking & Management module adds a persistent application-management layer to the AI Career Companion Agent.

It supports the complete basic lifecycle of an internship/job application: **creation, status management, search, filtering, deadline monitoring, interview tracking, follow-up information, generated document storage, updating, deletion, and dashboard reporting**.

Combined with the project's RAG, matching, skill-gap, application-generation, interview, and career-assistant components, the tracker enables the system to move beyond job recommendation toward an integrated student career workflow.
