

export const api = () => {

    let url = 'http://192.168.254.103:8080/api/'

    const get_appointments = async (): Promise<any> => {  
        const response = await fetch(url + 'appointment/get/all');
        const data = await response.json();
        return data;
    }

    return {
        get_appointments,
    } 

}

export default api;