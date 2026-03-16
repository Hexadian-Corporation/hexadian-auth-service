import { useParams } from "react-router";

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">User Detail</h1>
      <p className="text-gray-500">User ID: {id}</p>
      <p className="text-gray-500">User detail view coming soon.</p>
    </div>
  );
}
