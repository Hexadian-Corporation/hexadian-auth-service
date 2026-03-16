const RSI_HANDLE_PATTERN = /^[A-Za-z0-9_-]{3,30}$/;
const MIN_PASSWORD_LENGTH = 8;

export interface ValidationErrors {
  username?: string;
  password?: string;
  confirmPassword?: string;
  rsiHandle?: string;
}

export function validateUsername(username: string): string | undefined {
  if (!username.trim()) {
    return "Username is required";
  }
  return undefined;
}

export function validatePassword(password: string): string | undefined {
  if (!password) {
    return "Password is required";
  }
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters`;
  }
  return undefined;
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): string | undefined {
  if (!confirmPassword) {
    return "Please confirm your password";
  }
  if (password !== confirmPassword) {
    return "Passwords do not match";
  }
  return undefined;
}

export function validateRsiHandle(handle: string): string | undefined {
  if (!handle.trim()) {
    return "RSI handle is required";
  }
  if (!RSI_HANDLE_PATTERN.test(handle)) {
    return "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)";
  }
  return undefined;
}

export function validateRegistrationForm(fields: {
  username: string;
  password: string;
  confirmPassword: string;
  rsiHandle: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};

  const usernameError = validateUsername(fields.username);
  if (usernameError) errors.username = usernameError;

  const passwordError = validatePassword(fields.password);
  if (passwordError) errors.password = passwordError;

  const confirmPasswordError = validateConfirmPassword(
    fields.password,
    fields.confirmPassword,
  );
  if (confirmPasswordError) errors.confirmPassword = confirmPasswordError;

  const rsiHandleError = validateRsiHandle(fields.rsiHandle);
  if (rsiHandleError) errors.rsiHandle = rsiHandleError;

  return errors;
}

export function hasErrors(errors: ValidationErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function validateLoginForm(fields: {
  username: string;
  password: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};

  const usernameError = validateUsername(fields.username);
  if (usernameError) errors.username = usernameError;

  if (!fields.password) {
    errors.password = "Password is required";
  }

  return errors;
}
