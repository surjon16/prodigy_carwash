import { IonPage, IonHeader, IonToolbar, IonTitle, IonContent, IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonAvatar, IonItem, IonLabel, IonTabBar, IonIcon, IonTab, IonTabButton, IonTabs } from '@ionic/react';
import { useEffect, useState } from 'react';
import { Appointment } from './pages/interfaces/models';
import './Appointments.css';

const url = 'http://192.168.254.103:8080'

const Appointments: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    fetch(url + '/api/appointment/get/all')
      .then(res => res.json())
      .then(result => {
        // Ensure we always have an array
        const data = result.data
        const list = Array.isArray(data) ? data : [data];
        setAppointments(list);
      })
      .catch(err => console.error(err));
  }, []);

  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>Appointments</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        {appointments.length === 0 && <p>No appointments available.</p>}
        {appointments.map(a => (
          <IonCard key={a.id}>
            <IonCardHeader>
              <IonCardTitle>{a.service.name} ({a.service.duration} min)</IonCardTitle>
            </IonCardHeader>
            <IonCardContent>
              <IonItem>
                <IonAvatar slot="start">
                  <img src={url + '/static/' + a.customer.account.image_profile} alt={a.customer.account.first_name} />
                </IonAvatar>
                <IonLabel>
                  <h2>Customer: {a.customer.account.first_name} {a.customer.account.last_name}</h2>
                  {a.customer.account.email && <p>Email: {a.customer.account.email}</p>}
                  {a.customer.account.phone_1 && <p>Phone: {a.customer.account.phone_1}</p>}
                </IonLabel>
              </IonItem>

              <p>Vehicle: {a.vehicle.type} - {a.vehicle.model} {a.vehicle.plate_number ? `(${a.vehicle.plate_number})` : ''}</p>
              <p>Bay: {a.bay.bay}</p>
              <p>Status: {a.status.status}</p>
              <p>Start: {new Date(a.start_time).toLocaleTimeString()}</p>
              <p>End: {new Date(a.end_time).toLocaleTimeString()}</p>

              <p>
                Staffs: {a.staffs.length > 0
                  ? a.staffs.map(s => `${s.account.first_name} ${s.account.last_name}`).join(', ')
                  : 'No staff assigned'}
              </p>
            </IonCardContent>
          </IonCard>
        ))}
      </IonContent>
    </IonPage>
  );
};

export default Appointments;
