// frontend/src/components/TestPage.tsx
// --- ИСПРАВЛЕННАЯ ВЕРСИЯ ---

import { useState } from 'react';
import { Button } from './ui/button';

// 1. ИСПРАВЛЕННЫЙ ИМПОРТ:
// Мы импортируем НЕ 'factCheckingService', а нашу новую функцию 'checkText'
import { checkText, AnalysisResult } from '../utils/factCheckingService';

export function TestPage() {
  const [testResult, setTestResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  const runApiTest = async () => {
    setIsLoading(true);
    setTestResult('Running test...');

    try {
      const testText = "This is a test of the API connection.";
      
      // 2. ИСПРАВЛЕННЫЙ ВЫЗОВ:
      // Мы вызываем 'checkText' напрямую, а не через объект
      const result: AnalysisResult = await checkText(testText);

      // Проверяем, что результат содержит нужные поля
      if (result && result.classification && result.explanation) {
        setTestResult(`SUCCESS! Received classification: ${result.classification}. Explanation starts with: "${result.explanation.substring(0, 30)}..."`);
      } else {
        throw new Error("API response is missing expected fields.");
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setTestResult(`FAILED! Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">API Connection Test Page</h1>
      <p className="mb-4">
        Click the button to send a test request to the <code>/analyze_mock</code> endpoint.
      </p>
      <Button onClick={runApiTest} disabled={isLoading}>
        {isLoading ? 'Testing...' : 'Run API Test'}
      </Button>
      
      {testResult && (
        <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-md">
          <h2 className="font-semibold">Test Result:</h2>
          <pre className="whitespace-pre-wrap break-all">{testResult}</pre>
        </div>
      )}
    </div>
  );
}