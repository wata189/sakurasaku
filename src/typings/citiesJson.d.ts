declare module "./assets/cities.json" {
  type City = {
    id: number;
    lat: number;
    lon: number;
    name: string;
  }
  type Cities = {
    cities: City[];
  }
  const cities: Cities;
  export default cities;
}