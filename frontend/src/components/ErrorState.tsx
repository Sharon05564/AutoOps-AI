function ErrorState({ message = "Something went wrong." }: { message?: string }) {
  return <div className="error-state">{message}</div>;
}

export default ErrorState;
