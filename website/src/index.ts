type Instance = {
  Name: string;
  Id: string;
  Type: string;
  State: string;
  AZ: string;
  PublicIps: string[];
  PrivateIps: string[];
};

type ApiResponse = {
  NextToken?: string;
  Instances: Instance[];
};

type DataTable = {
  NextToken?: string;
  Instances: Instance[];
  PageSize: number;
};

let page: number = 0;
const dataTable: DataTable = {
  Instances: [],
  PageSize: 10,
};
const auth: { [key: string]: string } = {};

const setLoggedInElementsVisibility = (authenticated: boolean) => {
  document.getElementById('dataView').hidden = !authenticated;
  document.getElementById('loginLink').hidden = authenticated;
};

const generateInstanceRow = (inst: Instance): string => `<tr>
    <th scope="row">${inst.Name}</th>
    <td>${inst.Id}</td>
    <td>${inst.Type}</td>
    <td>${inst.State}</td>
    <td>${inst.AZ}</td>
    <td>${inst.PublicIps.join('\n')}</td>
    <td>${inst.PrivateIps.join('\n')}</td>
  </tr>`;

const displayInstances = (Instances: Instance[]) => {
  const tbody = document.getElementById('dataTbody');
  tbody.innerHTML = '';
  Instances.forEach((Instance) => {
    tbody.innerHTML += generateInstanceRow(Instance);
  });
};

const loadTableData = async (NextToken?: string) => {
  let url = process.env.API_DOMAIN;
  if (NextToken) {
    url += `?${new URLSearchParams({ NextToken })}`;
    const next = document.getElementById('page-more');
    const last = new HTMLOListElement();
    last.className = 'page-item';
    last.innerHTML = `<a class="page-link" href="#">${page + 1}</a>`;
    document.getElementById('page-bar').insertBefore(next, last);
  }
  fetch(url)
    .then((response) => {
      if (!response.ok) {
        if (response.status >= 400 && response.status < 500) {
          setLoggedInElementsVisibility(false);
          throw new Error(
            `Cannot get data as not logged in: ${response.status}`,
          );
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((body: ApiResponse) => {
      try {
        if ('NextToken' in body) {
          dataTable.NextToken = body.NextToken;
        } else {
          delete dataTable.NextToken;
          document.getElementById('page-more').hidden = true;
          if (page === 0) {
            document.getElementById('page-bar').hidden = true;
          }
        }
        body.Instances.map((Instance: Instance) => dataTable.Instances.push(Instance));
        displayInstances(body.Instances);
      } catch (error) {
        throw new Error(`Error handling api response: ${body} ${error}`);
      }
    });
};

const tryLogin = async (authString: string) => {
  authString.slice(1).split('&').forEach((ent) => {
    const [key, value] = ent.split('=');
    auth[key] = value;
  });
  // Clear credentials from location to prevent leaks
  window.location.hash = '';
  setLoggedInElementsVisibility(true);
  await loadTableData();
};

const setLoginLink = () => {
  document.getElementById('loginLink').setAttribute('href', process.env.LOGIN_URL);
};

const onLoad = async () => {
  if (window.location.hash.length > 1) {
    await tryLogin(window.location.hash);
  }
  setLoginLink();
};

const reloadData = async () => {
  page = 0;
  dataTable.Instances = [];
  document.getElementById('dataTbody').innerHTML = '';
  await loadTableData();
};

const logout = () => {
  setLoggedInElementsVisibility(false);
  page = 0;
  dataTable.Instances = [];
  Object.keys(auth).forEach((key) => delete auth[key]);
};

if (typeof window !== 'undefined') {
  window.onload = () => {
    onLoad();
  };
}

export {
  reloadData,
  logout,
  setLoggedInElementsVisibility,
  displayInstances,
  loadTableData,
  onLoad,
  tryLogin,
  DataTable,
  ApiResponse,
};
