interface BehumanLogoProps {
  className?: string;
  size?: number;
}

const BehumanLogo = ({ className = "", size = 48 }: BehumanLogoProps) => {
  return (
    <svg
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      className={className}
    >
      <path
        d="M50 5 C55 5, 65 20, 70 30 C75 40, 90 45, 95 50 C90 55, 75 60, 70 70 C65 80, 55 95, 50 95 C45 95, 35 80, 30 70 C25 60, 10 55, 5 50 C10 45, 25 40, 30 30 C35 20, 45 5, 50 5 Z"
        fill="hsl(var(--primary))"
      />
    </svg>
  );
};

export default BehumanLogo;
