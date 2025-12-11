export const handleApiError = (error: Error): string => {
  const message = error.message.toLowerCase();
  
  if (message.includes('fetch') || message.includes('network')) {
    return 'Network connection failed. Please check your internet connection.';
  }
  
  if (message.includes('404')) {
    return 'The requested data was not found.';
  }
  
  if (message.includes('500')) {
    return 'Server error occurred. Please try again later.';
  }
  
  if (message.includes('timeout')) {
    return 'Request timed out. Please try again.';
  }
  
  return 'An unexpected error occurred. Please try again.';
};

export const isNetworkError = (error: Error): boolean => {
  const message = error.message.toLowerCase();
  return message.includes('fetch') || message.includes('network') || message.includes('connection');
};

export const shouldRetry = (error: Error): boolean => {
  // Don't retry on 4xx errors (client errors)
  if (error.message.includes('400') || error.message.includes('401') || error.message.includes('403') || error.message.includes('404')) {
    return false;
  }
  
  // Retry on network errors and 5xx errors
  return isNetworkError(error) || error.message.includes('500') || error.message.includes('timeout');
};