import { describe, it, expect } from "vitest";
import {
  validateUsername,
  validatePassword,
  validateConfirmPassword,
  validateRsiHandle,
  validateRegistrationForm,
  hasErrors,
} from "@/lib/validation";

describe("validateUsername", () => {
  it("returns error for empty string", () => {
    expect(validateUsername("")).toBe("Username is required");
  });

  it("returns error for whitespace-only string", () => {
    expect(validateUsername("   ")).toBe("Username is required");
  });

  it("returns undefined for valid username", () => {
    expect(validateUsername("testuser")).toBeUndefined();
  });
});

describe("validatePassword", () => {
  it("returns error for empty string", () => {
    expect(validatePassword("")).toBe("Password is required");
  });

  it("returns error for short password", () => {
    expect(validatePassword("abc")).toBe(
      "Password must be at least 8 characters",
    );
  });

  it("returns error for 7-character password", () => {
    expect(validatePassword("1234567")).toBe(
      "Password must be at least 8 characters",
    );
  });

  it("returns undefined for 8-character password", () => {
    expect(validatePassword("12345678")).toBeUndefined();
  });

  it("returns undefined for long password", () => {
    expect(validatePassword("a-very-long-password")).toBeUndefined();
  });
});

describe("validateConfirmPassword", () => {
  it("returns error for empty confirm password", () => {
    expect(validateConfirmPassword("password", "")).toBe(
      "Please confirm your password",
    );
  });

  it("returns error when passwords do not match", () => {
    expect(validateConfirmPassword("password1", "password2")).toBe(
      "Passwords do not match",
    );
  });

  it("returns undefined when passwords match", () => {
    expect(validateConfirmPassword("password", "password")).toBeUndefined();
  });
});

describe("validateRsiHandle", () => {
  it("returns error for empty string", () => {
    expect(validateRsiHandle("")).toBe("RSI handle is required");
  });

  it("returns error for whitespace-only string", () => {
    expect(validateRsiHandle("   ")).toBe("RSI handle is required");
  });

  it("returns error for handle shorter than 3 characters", () => {
    expect(validateRsiHandle("ab")).toBe(
      "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)",
    );
  });

  it("returns error for handle with invalid characters", () => {
    expect(validateRsiHandle("test@user")).toBe(
      "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)",
    );
  });

  it("returns error for handle with spaces", () => {
    expect(validateRsiHandle("test user")).toBe(
      "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)",
    );
  });

  it("returns error for handle longer than 30 characters", () => {
    expect(validateRsiHandle("a".repeat(31))).toBe(
      "RSI handle must be 3–30 characters (letters, numbers, hyphens, underscores)",
    );
  });

  it("returns undefined for valid 3-character handle", () => {
    expect(validateRsiHandle("abc")).toBeUndefined();
  });

  it("returns undefined for valid 30-character handle", () => {
    expect(validateRsiHandle("a".repeat(30))).toBeUndefined();
  });

  it("returns undefined for handle with hyphens and underscores", () => {
    expect(validateRsiHandle("test-user_123")).toBeUndefined();
  });
});

describe("validateRegistrationForm", () => {
  it("returns no errors for valid form", () => {
    const errors = validateRegistrationForm({
      username: "testuser",
      password: "password123",
      confirmPassword: "password123",
      rsiHandle: "test-handle",
    });
    expect(errors).toEqual({});
  });

  it("returns all errors for empty form", () => {
    const errors = validateRegistrationForm({
      username: "",
      password: "",
      confirmPassword: "",
      rsiHandle: "",
    });
    expect(errors.username).toBeDefined();
    expect(errors.password).toBeDefined();
    expect(errors.confirmPassword).toBeDefined();
    expect(errors.rsiHandle).toBeDefined();
  });

  it("returns multiple specific errors", () => {
    const errors = validateRegistrationForm({
      username: "user",
      password: "short",
      confirmPassword: "mismatch",
      rsiHandle: "ab",
    });
    expect(errors.username).toBeUndefined();
    expect(errors.password).toBe("Password must be at least 8 characters");
    expect(errors.confirmPassword).toBe("Passwords do not match");
    expect(errors.rsiHandle).toBeDefined();
  });
});

describe("hasErrors", () => {
  it("returns false for empty errors object", () => {
    expect(hasErrors({})).toBe(false);
  });

  it("returns true when errors exist", () => {
    expect(hasErrors({ username: "Required" })).toBe(true);
  });
});
