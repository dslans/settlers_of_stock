import React from 'react';
import { render, screen } from '@testing-library/react';

// Simple test to verify Jest setup
describe('Simple Test', () => {
  it('should render a simple component', () => {
    const SimpleComponent = () => <div>Hello Test</div>;
    
    render(<SimpleComponent />);
    
    expect(screen.getByText('Hello Test')).toBeInTheDocument();
  });
  
  it('should perform basic assertions', () => {
    expect(1 + 1).toBe(2);
    expect('hello').toMatch(/hello/);
    expect([1, 2, 3]).toHaveLength(3);
  });
});