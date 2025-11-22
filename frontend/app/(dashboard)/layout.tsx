import { Sidebar } from '@/components/dashboard/sidebar';
import { Navbar } from '@/components/dashboard/navbar';
import { BottomNav } from '@/components/dashboard/bottom-nav';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar - скрыт на мобильных, виден на планшетах и десктопах */}
      <Sidebar />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-y-auto bg-background p-4 md:p-6 pb-16 md:pb-6">
          {children}
        </main>
      </div>

      {/* Bottom Navigation - только для мобильных устройств */}
      <BottomNav />
    </div>
  );
}
