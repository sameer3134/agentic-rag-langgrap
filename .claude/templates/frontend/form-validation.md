---
model: claude-sonnet-4-0
complexity: advanced
priority: high
tags: ["forms", "frontend", "validation", "components"]
depends_on: []
chains_to: []
skip_if: ["no_frontend"]
version: 1.0.0

---

$ARGUMENTS

## Graphify Context
{{GRAPH_IMPORTANCE_LOGIC}}
> Instruction to future Claude: "If this module is identified as a 'Core Node' by Graphify, apply 2x stricter linting and testing rules."

# Form Validation & Handling Architecture

This template defines the complete form validation and handling system for our {{FE_FRAMEWORK}} frontend. All form components live under `{{FE_PATH_COMPONENTS}}/forms/`, hooks under `{{FE_PATH_HOOKS}}/`, validation utilities under `{{FE_PATH_UTILS}}/validation/`, and tests under `{{FE_PATH_TESTS}}/forms/`. Follow {{NAMING_CONVENTION}} for all files and exports.

---

## 1. Form Library Selection & Patterns

### Controlled vs Uncontrolled Strategy

Use **controlled components** as the default for all forms in {{FE_FRAMEWORK}}. Reserve uncontrolled components only for performance-critical scenarios (large lists, real-time input fields) where re-render cost is measurable.

### Form State Architecture

- Centralize form state through a dedicated form library (React Hook Form, Formik, or equivalent for {{FE_FRAMEWORK}}).
- Integrate form state with {{FE_STATE_MANAGER}} only when form values must be shared across routes or persisted beyond the form lifecycle.
- Keep ephemeral form state (dirty flags, touched fields, submission count) local to the form instance.
- Implement a `useFormDefaults` hook at `{{FE_PATH_HOOKS}}/useFormDefaults.{{FE_LANGUAGE}}` that merges server-fetched defaults with local overrides.

```{{FE_LANGUAGE}}
// {{FE_PATH_HOOKS}}/useFormDefaults.{{FE_LANGUAGE}}
// Merge remote defaults with local draft state from {{FE_STATE_MANAGER}}
export function useFormDefaults<T>(endpoint: string, fallback: T): FormDefaults<T> {
  // Implementation: fetch from {{BE_PATH_API}}, merge with {{FE_STATE_MANAGER}} draft
}
```

### File Organization

```
{{FE_PATH_SRC}}/
  {{FE_PATH_COMPONENTS}}/forms/
    shared/            # Reusable input primitives (TextInput, Select, Checkbox, etc.)
    wizards/           # Multi-step form containers
    dynamic/           # Schema-driven form renderers
  {{FE_PATH_HOOKS}}/
    useFormDefaults.{{FE_LANGUAGE}}
    useFieldValidation.{{FE_LANGUAGE}}
    useFormSubmission.{{FE_LANGUAGE}}
    useWizardState.{{FE_LANGUAGE}}
    useFileUpload.{{FE_LANGUAGE}}
  {{FE_PATH_UTILS}}/validation/
    schemas/           # Zod/Yup/Joi schema definitions
    messages/          # i18n error message catalogs
    transforms.{{FE_LANGUAGE}}
```

---

## 2. Validation Schema Design

### Schema Library & {{FE_LANGUAGE}} Integration

Define all validation schemas in `{{FE_PATH_UTILS}}/validation/schemas/` using Zod (preferred), Yup, or Joi. Every schema must produce a corresponding {{FE_LANGUAGE}} type via inference so that form values and validation errors are fully typed.

```{{FE_LANGUAGE}}
// {{FE_PATH_UTILS}}/validation/schemas/userProfile.{{FE_LANGUAGE}}
import { z } from "zod";

export const userProfileSchema = z.object({
  displayName: z.string().min(2).max(64),
  email: z.string().email(),
  age: z.number().int().min(13).max(150).optional(),
  bio: z.string().max(500).optional(),
});

// Inferred type — use this in components, never hand-write a duplicate interface
export type UserProfile = z.infer<typeof userProfileSchema>;
```

### Schema Composition Rules

- **Shared field schemas**: Extract common fields (email, phone, address) into `{{FE_PATH_UTILS}}/validation/schemas/fields.{{FE_LANGUAGE}}` and compose via `.merge()` or `.extend()`.
- **Conditional schemas**: Use `.refine()` or `.superRefine()` for cross-field logic; never validate cross-field rules at the individual field level.
- **Transform schemas**: Apply `.transform()` for normalization (trimming, lowercasing emails) so that the validated output is always clean.
- **Coercion schemas**: Use `z.coerce` for values originating from URL params or form inputs that arrive as strings.

---

## 3. Client-Side Validation

### Field-Level Validation

Trigger field validation on `blur` by default. Switch to `onChange` only after the field has been touched and contains an error (progressive validation). Implement via `{{FE_PATH_HOOKS}}/useFieldValidation.{{FE_LANGUAGE}}`.

### Form-Level Validation

Run full-schema validation on submit. If the schema parse fails, map each `ZodIssue` path to the corresponding field name and set errors in the form state.

### Cross-Field Validation

```{{FE_LANGUAGE}}
// Example: confirm-password must match password
const signupSchema = z
  .object({
    password: z.string().min(8),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
```

### Async Validation

For uniqueness checks (username, email), debounce the request by 400ms and call `{{BE_PATH_API}}/validate/<field>`. Show a loading indicator on the field while the request is in-flight. Cache recent results to avoid redundant network calls.

```{{FE_LANGUAGE}}
// {{FE_PATH_HOOKS}}/useAsyncFieldValidation.{{FE_LANGUAGE}}
export function useAsyncFieldValidation(
  endpoint: string,
  debounceMs: number = 400
) {
  // Returns { validate, isValidating, error }
  // Calls {{BE_PATH_API}}/validate/{field} with debounce
}
```

---

## 4. Server-Side Validation Integration

### Error Mapping from {{BE_FRAMEWORK}} Responses

The backend ({{BE_FRAMEWORK}}) returns validation errors in a standard envelope:

```json
{
  "status": 422,
  "errors": {
    "fieldName": ["Error message 1", "Error message 2"],
    "nested.field.path": ["Error message"]
  }
}
```

Map these to form field errors using a `mapServerErrors` utility in `{{FE_PATH_UTILS}}/validation/transforms.{{FE_LANGUAGE}}`:

```{{FE_LANGUAGE}}
// Converts {{BE_FRAMEWORK}} error envelope to form-library error format
export function mapServerErrors(
  serverErrors: Record<string, string[]>
): FieldErrors {
  return Object.entries(serverErrors).reduce((acc, [path, messages]) => {
    acc[path] = { type: "server", message: messages[0] };
    return acc;
  }, {} as FieldErrors);
}
```

### Conflict Resolution

When both client and server errors exist for the same field, display the server error. Clear server errors for a field as soon as the user modifies that field's value.

---

## 5. Multi-Step / Wizard Forms

### State Persistence

Store wizard state in {{FE_STATE_MANAGER}} and persist to `sessionStorage` so that a page refresh does not lose progress. Each step's data is validated independently before advancing.

```{{FE_LANGUAGE}}
// {{FE_PATH_HOOKS}}/useWizardState.{{FE_LANGUAGE}}
export function useWizardState<TSteps extends Record<string, z.ZodSchema>>(config: {
  steps: TSteps;
  persistKey: string;
}) {
  // Returns { currentStep, stepData, goNext, goBack, isStepValid, progress }
}
```

### Step Validation

- Validate the current step's schema before allowing navigation to the next step.
- Allow backward navigation without validation so users can review previous entries.
- On final submission, run the merged schema (all steps combined) to catch cross-step dependencies.

### Progress Tracking

Render a progress bar or step indicator that reflects: completed steps, current step, and remaining steps. Mark steps with validation errors in a visually distinct state (e.g., red dot). Ensure the progress indicator is announced to screen readers via `aria-live="polite"`.

---

## 6. Dynamic Forms

### Schema-Driven Rendering

Support rendering forms from a JSON schema fetched from `{{BE_PATH_API}}/form-schemas/<formId>`. The renderer at `{{FE_PATH_COMPONENTS}}/forms/dynamic/DynamicFormRenderer.{{FE_LANGUAGE}}` maps each schema field type to a registered component.

```{{FE_LANGUAGE}}
// Field type registry
const fieldRegistry: Record<string, ComponentType<FieldProps>> = {
  text: TextInput,
  select: SelectInput,
  checkbox: CheckboxInput,
  date: DatePicker,
  file: FileUploadInput,
  group: FieldGroup,
  repeatable: RepeatableSection,
};
```

### Conditional Fields

Use a `visibleWhen` predicate in the schema to control field visibility. Evaluate predicates reactively so fields appear/disappear as dependencies change. Hidden fields must be excluded from validation and submission payloads.

### Repeatable Sections

Implement add/remove controls for array fields. Validate each item against the item schema independently. Set sensible min/max item counts from the schema definition.

---

## 7. File Upload Handling

### Implementation at `{{FE_PATH_HOOKS}}/useFileUpload.{{FE_LANGUAGE}}`

```{{FE_LANGUAGE}}
export function useFileUpload(config: {
  endpoint: string;        // {{BE_PATH_API}}/uploads
  maxSizeMB: number;
  acceptedTypes: string[];
  chunkSizeKB?: number;    // Enable chunked upload when set
}) {
  // Returns { upload, progress, preview, cancel, error, isUploading }
}
```

### Features

- **Drag-and-drop**: Wrap the drop zone with `onDragOver`, `onDrop` handlers. Provide visual feedback (border highlight) using {{FE_STYLE_SYSTEM}}.
- **Preview**: Generate `URL.createObjectURL` previews for images. For non-image files, show an icon and filename.
- **Progress**: Track `XMLHttpRequest` or `fetch` upload progress and expose a 0-100 percentage.
- **Chunked upload**: For files exceeding the chunk threshold, split into `chunkSizeKB` slices and upload sequentially with resume capability. Send a final merge request to `{{BE_PATH_API}}/uploads/merge`.
- **Validation**: Check file size and MIME type client-side before uploading. Reject invalid files immediately with a descriptive error.

---

## 8. Accessibility in Forms

### Error Announcements

- Wrap form error summaries in a container with `role="alert"` so screen readers announce errors immediately upon submission.
- Use `aria-describedby` on each input to link it to its error message element.
- On submission failure, move focus to the first field with an error.

### ARIA & Label Association

- Every input must have a visible `<label>` with a matching `htmlFor`/`id` pair. Do not rely on `placeholder` as the sole label.
- Group related fields (e.g., address components) with `<fieldset>` and `<legend>`.
- Mark required fields with `aria-required="true"` and a visual indicator.
- Use `aria-invalid="true"` on fields that currently have validation errors.

### Focus Management

- After async validation completes with an error, return focus to the validated field.
- In wizard forms, move focus to the first input of the new step on navigation.
- Trap focus inside modal forms until they are dismissed.

### Audit

Run `{{FE_A11Y_TOOL}}` in the CI pipeline (`{{FE_LINT_COMMAND}}`) and fail the build on any form-related a11y violation. Test with {{FE_BROWSER}} and at least one screen reader during manual QA.

---

## 9. Form Performance

### Debounced Validation

Debounce `onChange` validation by 300ms for text inputs. Do not debounce `onBlur` or `onSubmit` validation. Use a shared `useDebouncedCallback` hook from `{{FE_PATH_HOOKS}}/`.

### Optimistic Submission

For low-risk mutations (e.g., profile updates), optimistically update the UI via {{FE_STATE_MANAGER}} while the request is in flight. Roll back on server error and display the server error message.

### Preventing Double Submit

- Disable the submit button and show a spinner while `isSubmitting` is `true`.
- Implement request deduplication: if a submit request is in-flight, ignore subsequent clicks rather than queuing them.
- Set a cooldown of 2 seconds after a successful submission before re-enabling the button.

### Render Optimization

- Isolate frequently re-rendering fields (e.g., character counters, live previews) into memoized child components.
- Use `shouldDirty` and `shouldTouch` flags judiciously to prevent unnecessary re-renders across unrelated fields.

---

## 10. Internationalization

### Translated Error Messages

Store error message templates in `{{FE_PATH_UTILS}}/validation/messages/<locale>.{{FE_LANGUAGE}}`. Each schema references message keys rather than hardcoded English strings.

```{{FE_LANGUAGE}}
// {{FE_PATH_UTILS}}/validation/messages/en.{{FE_LANGUAGE}}
export const validationMessages = {
  required: "This field is required",
  email: "Please enter a valid email address",
  minLength: "Must be at least {{min}} characters",
  maxLength: "Must be no more than {{max}} characters",
  passwordMismatch: "Passwords do not match",
  uniqueConflict: "This {{field}} is already taken",
} as const;
```

### RTL Support

- Apply `dir="rtl"` on the form container when the active locale is RTL.
- Use logical CSS properties (`margin-inline-start` instead of `margin-left`) in {{FE_STYLE_SYSTEM}}.
- Mirror the layout of inline error icons and validation indicators for RTL locales.

### Locale-Aware Formatting

- Format date inputs according to the user's locale (`Intl.DateTimeFormat`).
- Format number inputs with locale-appropriate decimal and thousands separators (`Intl.NumberFormat`).
- Validate phone numbers against locale-specific patterns.

---

## 11. Testing Forms with {{FE_TEST_FRAMEWORK}}

### Test File Location

Place all form tests in `{{FE_PATH_TESTS}}/forms/`. Name test files `<ComponentName>.test.{{FE_LANGUAGE}}`.

### User Interaction Simulation

```{{FE_LANGUAGE}}
// {{FE_PATH_TESTS}}/forms/UserProfileForm.test.{{FE_LANGUAGE}}
describe("UserProfileForm", () => {
  it("shows validation error when email is invalid", async () => {
    render(<UserProfileForm />);
    const emailInput = screen.getByLabelText(/email/i);
    await userEvent.type(emailInput, "not-an-email");
    await userEvent.tab(); // trigger blur validation
    expect(screen.getByRole("alert")).toHaveTextContent(/valid email/i);
  });

  it("submits successfully with valid data", async () => {
    const onSubmit = vi.fn();
    render(<UserProfileForm onSubmit={onSubmit} />);
    await userEvent.type(screen.getByLabelText(/name/i), "Jane Doe");
    await userEvent.type(screen.getByLabelText(/email/i), "jane@example.com");
    await userEvent.click(screen.getByRole("button", { name: /submit/i }));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ displayName: "Jane Doe", email: "jane@example.com" })
    );
  });

  it("prevents double submission", async () => {
    const onSubmit = vi.fn(() => new Promise((r) => setTimeout(r, 1000)));
    render(<UserProfileForm onSubmit={onSubmit} />);
    // Fill required fields...
    const submitBtn = screen.getByRole("button", { name: /submit/i });
    await userEvent.click(submitBtn);
    await userEvent.click(submitBtn);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
```

### Validation Coverage Requirements

- Every schema in `{{FE_PATH_UTILS}}/validation/schemas/` must have a corresponding test file exercising all rules.
- Test both valid and invalid inputs for each field.
- Test cross-field validations with boundary values.
- Test server error mapping with mocked {{BE_FRAMEWORK}} error responses.
- Test async validation with mocked API responses (success, conflict, network failure).

### Running Tests

```bash
{{FE_TEST_COMMAND}}             # Run all form tests
{{FE_LINT_COMMAND}}             # Lint form components and hooks
```

---

## 12. Error UX Patterns

### Inline Errors

- Display errors directly below the input field, inside a `<span>` with `role="alert"` and a class from {{FE_STYLE_SYSTEM}} that applies red text and an error icon.
- Show inline errors on blur (after first interaction) and on submit.
- Clear the error as soon as the field value becomes valid (live clearing).

### Summary Banners

- On form submission failure, render an error summary banner at the top of the form listing all field errors as anchor links. Clicking an error link scrolls to and focuses the corresponding field.
- The banner must have `role="alert"` and `tabindex="-1"` so it receives focus automatically after a failed submission.

### Toast Notifications

- Use toasts for non-field-specific errors (network failures, server 500s, rate limits).
- Toasts should auto-dismiss after 8 seconds but remain on hover.
- Provide a dismiss button accessible via keyboard.
- Never use toasts as the sole indicator for field-level validation errors.

### Error State Hierarchy

1. **Field inline error** — for individual field validation failures.
2. **Error summary banner** — aggregated view after a failed form submission.
3. **Toast notification** — transient alerts for system-level or network errors.
4. **Modal dialog** — for irrecoverable errors that require user acknowledgment before proceeding.

---

## Self-Hydration Checklist

Before marking this template as hydrated for a project, verify:

- [ ] All `{{PLACEHOLDER}}` tokens have been replaced with project-specific values.
- [ ] Validation schemas compile with zero {{FE_LANGUAGE}} errors.
- [ ] At least one form component renders, validates, and submits correctly end-to-end.
- [ ] `{{FE_TEST_COMMAND}}` passes with full coverage on the validation schemas.
- [ ] `{{FE_A11Y_TOOL}}` reports zero critical violations on all form views.
- [ ] RTL layout renders correctly for at least one RTL locale.
- [ ] File upload works with both small files and chunked uploads.
- [ ] Server error mapping correctly displays {{BE_FRAMEWORK}} validation errors inline.
- [ ] Wizard form state survives a full page refresh via `sessionStorage`.
- [ ] Double-submit prevention is verified under simulated slow network conditions.
