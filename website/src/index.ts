type Instance = {
  Name: string;
  Id: string;
  Type: string;
  State: string;
  AZ: string;
  PublicIps: string[];
  PrivateIps: string[];
};

type RowData = {
  Name: string;
  Id: string;
  Type: string;
  State: string;
  AZ: string;
  PublicIps: string
  PrivateIps: string
};

type ApiResponse = {
  NextToken?: string;
  Instances: Instance[];
};

type AjaxParms = {
  success: (data: any[]) => any
};

const setLoggedInElementsVisibility = (authenticated: boolean) => {
  document.getElementById('dataView').hidden = !authenticated;
  document.getElementById('loginLink').hidden = authenticated;
};

const logout = () => {
  setLoggedInElementsVisibility(false);
  localStorage.removeItem('Authorization');
};

const login = () => document.getElementById('loginLink').click();

const readCredentials = (authString: string) => {
  if (authString.includes('id_token')) {
    localStorage.setItem(
      'Authorization',
      authString.split('id_token=')[1].split('&')[0],
    );
    setLoggedInElementsVisibility(true);
  }
  window.location.hash = '';
};

const parseApiResponse = (response: Response) => {
  if (!response.ok) {
    if (response.status >= 400 && response.status < 500) {
      console.warn(`Cannot get data as not logged in: ${response.status}`);
      logout();
      login();
      throw Error('Not Authenticated');
    }
  }
  return response.json();
};

const parseJsonResponse = (
  body: ApiResponse,
  data: RowData[],
  params: AjaxParms,
  search: URLSearchParams,
) => {
  setLoggedInElementsVisibility(true);
  body.Instances.forEach((Instance) => {
    data.push({
      ...Instance,
      PrivateIps: Instance.PrivateIps.join('\n'),
      PublicIps: Instance.PublicIps.join('\n'),
    });
  });
  if ('NextToken' in body) {
    search.set('NextToken', body.NextToken);
  } else {
    params.success(data);
    search.delete('NextToken');
  }
};

const fetchAllData = async (params: AjaxParms) => {
  const data: RowData[] = [];
  const search = new URLSearchParams({ MaxResults: '1000' });
  try {
    do {
      /* eslint-disable no-await-in-loop */
      await fetch(`https://{{API_DOMAIN}}/?${search}`, {
        headers: [['Authorization', localStorage.getItem('Authorization')]],
      })
        .then(parseApiResponse)
        .then((body) => {
          parseJsonResponse(body, data, params, search);
        });
    } while (search.has('NextToken'));
  } catch {
    console.error('Error accessing API');
  }
};

async function ajaxRequest(params: AjaxParms) {
  readCredentials(window.location.hash);
  await fetchAllData(params);
}

function buttons() {
  return {
    btnLogOut: {
      text: 'Log Out',
      icon: 'bi-box-arrow-right',
      event: logout,
    },
  };
}

export {
  setLoggedInElementsVisibility,
  logout,
  login,
  readCredentials,
  parseApiResponse,
  parseJsonResponse,
  fetchAllData,
  ajaxRequest,
  buttons,
  ApiResponse,
  Instance,
  RowData,
  AjaxParms,
};
