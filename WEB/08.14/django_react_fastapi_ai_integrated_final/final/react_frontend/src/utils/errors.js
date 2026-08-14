export function formatFormErrors(error) {
  const errors = error?.data?.errors;
  if (!errors) return error?.message || '처리 중 오류가 발생했습니다.';
  return Object.entries(errors).map(([field, messages]) => `${field}: ${messages.join(' ')}`).join('\n');
}
