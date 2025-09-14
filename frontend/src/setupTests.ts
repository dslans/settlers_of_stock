// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock Chart.js modules that cause issues in Jest
jest.mock('chartjs-adapter-date-fns', () => ({}));
jest.mock('chartjs-plugin-zoom', () => ({}));
jest.mock('chartjs-plugin-annotation', () => ({}));
jest.mock('chartjs-chart-financial', () => ({
  CandlestickController: jest.fn(),
  CandlestickElement: jest.fn(),
  OhlcController: jest.fn(),
  OhlcElement: jest.fn(),
}));

// Mock Chart.js
jest.mock('chart.js', () => ({
  Chart: {
    register: jest.fn(),
  },
  CategoryScale: jest.fn(),
  LinearScale: jest.fn(),
  TimeScale: jest.fn(),
  Title: jest.fn(),
  Tooltip: jest.fn(),
  Legend: jest.fn(),
  BarElement: jest.fn(),
  LineElement: jest.fn(),
  PointElement: jest.fn(),
}));

// Mock react-chartjs-2
jest.mock('react-chartjs-2', () => ({
  Chart: jest.fn().mockImplementation(({ data, options, ...props }) => {
    const mockReact = require('react');
    return mockReact.createElement('div', {
      'data-testid': 'mock-chart',
      'data-chart-type': props.type,
      children: [
        mockReact.createElement('div', {
          'data-testid': 'chart-data',
          key: 'data',
          children: JSON.stringify(data || {})
        }),
        mockReact.createElement('div', {
          'data-testid': 'chart-options',
          key: 'options',
          children: JSON.stringify(options || {})
        })
      ]
    });
  }),
}));