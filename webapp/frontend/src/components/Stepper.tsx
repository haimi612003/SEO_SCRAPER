import type { Step } from "../types";

interface StepCircleProps {
  n: number;
  label: string;
  isActive: boolean;
  isDone: boolean;
}

function StepCircle({ n, label, isActive, isDone }: StepCircleProps) {
  const circleClass = "step-circle" + (isActive ? " active" : isDone ? " done" : "");
  const labelClass = "step-label" + (isActive ? " active" : isDone ? " done" : "");
  return (
    <div className="step">
      <div className={circleClass}>{isDone ? "✓" : n}</div>
      <div className={labelClass}>{label}</div>
    </div>
  );
}

interface StepperProps {
  step: Step;
}

export default function Stepper({ step }: StepperProps) {
  const isSetup = step === "setup";
  const isRunning = step === "running";
  const isResults = step === "results";
  return (
    <div className="stepper">
      <StepCircle n={1} label="Cấu hình" isActive={isSetup} isDone={!isSetup} />
      <div className="step-line"></div>
      <StepCircle n={2} label="Đang chạy" isActive={isRunning} isDone={isResults} />
      <div className="step-line"></div>
      <StepCircle n={3} label="Kết quả" isActive={isResults} isDone={false} />
    </div>
  );
}
