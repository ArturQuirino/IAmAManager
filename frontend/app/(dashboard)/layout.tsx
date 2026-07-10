import { DashboardNav } from '@/components/DashboardNav';

// Shared chrome for every in-game screen: a persistent navigation bar above the
// page content. Auth is enforced per page (via useAuth), so the nav simply
// links between the protected routes.
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <DashboardNav />
      {children}
    </div>
  );
}
