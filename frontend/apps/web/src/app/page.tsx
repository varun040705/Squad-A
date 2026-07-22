import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import PageContainer from "@/components/layout/PageContainer";

export default function HomePage() {
  return (
    <>
      <Header />

      <PageContainer>
        <h1>Ouantum AI Sensor Fusion</h1>

        <p>
          Enterprise AI platform built with Next.js 16, FastAPI,
          PostgreSQL and Redis.
        </p>

        <br />

        <h2>Modules</h2>

        <ul>
          <li>Authentication</li>
          <li>Dashboard</li>
          <li>Projects</li>
          <li>Reports</li>
          <li>Notifications</li>
          <li>Uploads</li>
          <li>Users</li>
          <li>Settings</li>
        </ul>

        <br />

        <h2>Backend</h2>

        <p>http://127.0.0.1:8000</p>

        <p>Swagger → /docs</p>
      </PageContainer>

      <Footer />
    </>
  );
}