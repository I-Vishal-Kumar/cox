'use client';

interface GaugeChartProps {
  value: number;
  maxValue?: number;
  label: string;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export default function GaugeChart({
  value,
  maxValue = 100,
  label,
  size = 'md',
  color = '#3b82f6',
}: GaugeChartProps) {
  const percentage = Math.min((value / maxValue) * 100, 100);
  const circumference = 2 * Math.PI * 40; // radius = 40
  const strokeDashoffset = circumference - (percentage / 100) * circumference * 0.75; // 75% of circle

  const sizeMap = {
    sm: { width: 80, fontSize: 'text-lg' },
    md: { width: 120, fontSize: 'text-2xl' },
    lg: { width: 160, fontSize: 'text-3xl' },
  };

  const { width, fontSize } = sizeMap[size];

  return (
    <div className="gauge-container" style={{ width, height: width }}>
      <svg
        viewBox="0 0 100 100"
        className="transform -rotate-[135deg]"
        style={{ width: '100%', height: '100%' }}
      >
        {/* Background arc */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="8"
          strokeDasharray={`${circumference * 0.75} ${circumference}`}
          strokeLinecap="round"
        />
        {/* Foreground arc */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="gauge-text">
        <div className={`gauge-value ${fontSize}`}>{value.toFixed(0)}%</div>
        <div className="gauge-label">{label}</div>
      </div>
    </div>
  );
}
